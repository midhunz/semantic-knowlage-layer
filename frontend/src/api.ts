/** Message from a failed response: FastAPI sends {"detail": "..."} or a list of validation errors. */
async function failure(res: Response): Promise<Error> {
  let msg = `${res.status}`;
  try {
    const body = await res.json();
    const d = body?.detail;
    msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: any) => `${(x.loc ?? []).slice(1).join(".")}: ${x.msg}`).join("; ") : msg;
  } catch { /* not JSON */ }
  const err = new Error(msg) as Error & { status: number };
  err.status = res.status;
  return err;
}

export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: "same-origin", ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/api/auth/")) window.dispatchEvent(new Event("sl:unauthorized"));
    if (res.status === 403) window.dispatchEvent(new CustomEvent("sl:forbidden", { detail: (await res.clone().json().catch(() => ({}))).detail }));
    throw await failure(res);
  }
  return res.json();
}
export const send = (method: string, path: string, body?: unknown) =>
  api(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });

export const errText = (e: unknown) => (e instanceof Error ? e.message : String(e));
