"""Spotting column names that probably hold personal or secret data (used to quarantine them)."""

import re

DEFAULT_KEYWORDS = ("email,phone,mobile,ssn,passport,national_id,emirates_id,eid,iban,address,birth,dob,"
                    "credit_card,card_number,cvv,password,passwd,secret,api_key,token,tax_id,salary")


def parse_keywords(text: str | None) -> list[str]:
    return [k.strip().lower() for k in re.split(r"[,\n;]", text or "") if k.strip()]


def _snake(name: str) -> str:
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)          # customerEmail -> customer_Email
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def sensitive_match(name: str, keywords: list[str]) -> str | None:
    """The first keyword that `name` matches, or None.

    Short keywords (email, dob, ssn…) must be a whole word so `adobe` or `lesson` don't match;
    longer or multi-word ones also match inside, at the start or at the end (`birthdate`, `accesstoken`).
    """
    n = _snake(name)
    words = set(n.split("_"))
    for raw in keywords:
        k = _snake(raw)
        if not k:
            continue
        if k in words:
            return raw
        if len(k) >= 5 and (k in n if "_" in k or len(k) >= 6 else n.startswith(k) or n.endswith(k)):
            return raw
    return None
