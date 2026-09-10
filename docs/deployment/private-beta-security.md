# Private beta security notes

This private-beta hardening layer adds two controls without changing local development behavior:

- Production same-origin protection rejects cross-site state-changing browser requests.
- Optional `GBO_INVITE_TOKEN` gating prevents uninvited account creation during private beta.

These controls complement authenticated, Secure, HttpOnly, SameSite=Lax sessions. They do not replace future password reset, email verification, rate limiting, or role-based access work.
