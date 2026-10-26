"""Operations CLI:  python -m app.cli <command>

  check            validate configuration and database state (exit 1 on problems)
  migrate          create/upgrade the schema (also adopts databases made before migrations existed)
  create-admin     create an administrator (prompts for the password unless --password is given)
  reset-password   set a new password for any user (generates a temporary one by default)
  backup           consistent copy of a SQLite database (for Postgres use scripts/backup.sh)
"""

import argparse
import getpass
import secrets
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app import migrate as mig
from app.auth import MIN_PASSWORD, hash_password
from app.config import settings, validate_for_production
from app.db import SessionLocal, describe_url
from app.db import engine as default_engine
from app.models import User, UserSession


def cmd_check(_: argparse.Namespace) -> int:
    ok = True
    print(f"environment : {settings.env}")
    print(f"database    : {describe_url()}")
    try:
        for w in validate_for_production():
            print(f"warning     : {w}")
    except RuntimeError as e:
        print(str(e)); ok = False
    try:
        rev, head = mig.current_revision(), mig.head_revision()
        shown = rev or ("created before migrations existed" if mig.is_legacy() else "not created")
        print(f"schema      : {shown} (latest {head}) -> {'up to date' if rev == head else 'NEEDS MIGRATION'}")
        ok &= rev == head
        if rev == head:
            with SessionLocal() as s:
                n = s.query(User).count()
            print(f"users       : {n}" + ("  (none: run create-admin)" if n == 0 else ""))
    except Exception as e:  # noqa: BLE001
        print(f"database    : cannot connect ({type(e).__name__}: {e})"); ok = False
    return 0 if ok else 1


def cmd_migrate(_: argparse.Namespace) -> int:
    print(mig.migrate())
    return 0


def _password(args: argparse.Namespace, confirm: bool) -> str:
    if args.password:
        pw = args.password
    else:
        pw = getpass.getpass("Password: ")
        if confirm and getpass.getpass("Repeat password: ") != pw:
            sys.exit("Passwords do not match")
    if len(pw) < MIN_PASSWORD:
        sys.exit(f"Password must be at least {MIN_PASSWORD} characters")
    return pw


def cmd_create_admin(args: argparse.Namespace) -> int:
    email = args.email.strip().lower()
    pw = _password(args, confirm=True)
    with SessionLocal() as s:
        if s.scalar(select(User).where(User.email == email)):
            sys.exit(f"{email} already exists. Use reset-password to change their password.")
        s.add(User(email=email, name=args.name or "", role="admin", password_hash=hash_password(pw)))
        s.commit()
    print(f"Administrator {email} created")
    return 0


def cmd_reset_password(args: argparse.Namespace) -> int:
    email = args.email.strip().lower()
    temp = None
    if args.password or args.prompt:
        pw = _password(args, confirm=True)
    else:
        temp = pw = secrets.token_urlsafe(9)
    with SessionLocal() as s:
        u = s.scalar(select(User).where(User.email == email))
        if u is None:
            sys.exit(f"No user {email}")
        u.password_hash, u.is_active = hash_password(pw), True
        u.must_change_password = temp is not None      # a generated password must be replaced at first sign-in
        s.query(UserSession).filter(UserSession.user_id == u.id).delete()
        s.commit()
    print(f"Password reset for {email}; all their sessions were ended.")
    if temp:
        print(f"Temporary password (must be changed at sign-in): {temp}")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    if not settings.is_sqlite:
        sys.exit("This command only handles SQLite. For Postgres use scripts/backup.sh (pg_dump).")
    src_path = default_engine.url.database
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"semantic_layer-{datetime.now():%Y%m%d-%H%M%S}.db"
    src, dst = sqlite3.connect(src_path), sqlite3.connect(dest)
    with dst:
        src.backup(dst)              # consistent even while the app is writing
    print(f"Backup written to {dest} ({dest.stat().st_size} bytes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("migrate").set_defaults(fn=cmd_migrate)
    a = sub.add_parser("create-admin"); a.add_argument("--email", required=True); a.add_argument("--name", default="")
    a.add_argument("--password", help="avoid: visible in shell history; omit to be prompted"); a.set_defaults(fn=cmd_create_admin)
    r = sub.add_parser("reset-password"); r.add_argument("--email", required=True)
    r.add_argument("--password", help="avoid: visible in shell history"); r.add_argument("--prompt", action="store_true", help="type the new password instead of generating one")
    r.set_defaults(fn=cmd_reset_password)
    b = sub.add_parser("backup"); b.add_argument("--out", default="backups"); b.set_defaults(fn=cmd_backup)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
