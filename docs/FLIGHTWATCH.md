# Flightwatch adapter and migration

Flightwatch uses authorization code + PKCE + state + nonce for browser sign-in.
TUI uses RFC 8628 device authorization; its public client never stores a client
secret. The current TUI retains its access token in memory only; reconnect and
approve again when it expires. Legacy shared-password login is removed.

The application maps `issuer + "\0" + sub` through SHA-256 to its local user ID.
Email is mutable. Browser sessions are opaque, stored hashed, HttpOnly/Secure/
SameSite=Lax and protected by CSRF tokens. JWT signatures, issuer, audience,
expiry, issued-at and authorization-code nonce are verified. The identity
service directory is refreshed every minute; only successful responses refresh
the maximum one-hour outage grace period. Explicit revocation invalidates
sessions and pauses tasks; restoring permission requires manual task resume.
An outage only suspends execution, so confirmed service recovery resumes work.

Every task has a nonempty owner. History, quotes, rounds and outbox inherit the
owner through task ID. Every task path, including cached email images, checks the
verified caller before returning content. Administrators cannot read other users'
trips. They manage only global service settings and per-user/per-mode quotas.

## Offline cutover

1. Save source/image versions and stop the complete API, scheduler and mail
   sender. Keep the edge in maintenance mode. Do not run a second writer.
2. Make a consistent full backup, including auth/demo/live/flyai databases,
   SMTP and provider configuration, existing deployment settings and image ID.
3. Read the intended owner's exact Casdoor subject from runtime/owner.json.
   Check that it belongs to the verified owner; never adopt the first visitor.
4. Run `flightwatch migrate-identity --issuer https://id.example.com --subject UUID`
   with `FLIGHTWATCH_DATA` pointing to the stopped deployment data directory.
5. The migration backs up SQLite files under before-identity/, sets version 1,
   preserves task IDs/relations and assigns old tasks to the explicit owner. It
   cancels unsent legacy mail and invalidates old shared sessions. Restarting
   the migration with the same owner is safe; a different owner is rejected.
   A failure leaves identity-migration.json, which prevents normal startup.
6. Copy runtime/flightwatch-client-secret to the deployment data directory as
   oidc-client-secret (0600, application UID). Apply runtime/flightwatch.env.
   Verify OIDC callback and TUI client configuration before enabling ingress.
7. Check table counts, IDs, foreign keys, owner distribution, and two fresh
   users with empty task lists. Test cookie and bearer paths, then restore
   scheduler/mail and remove maintenance mode.
8. On failure, keep maintenance enabled. Restore all original databases and
   source/image together from the pre-cutover backup, not just tasks. Do not
   replay cancelled legacy mail to newly changed addresses.

Default quota is five running tasks per mode per user. Creation, resume and
reviving expired tasks use SQLite write transactions. Existing global provider
budgets, limits and resource lock remain shared. Scheduled collection rotates
between eligible users. Shared SMTP sends to each task owner's currently
verified email; old pending routes are cancelled on email changes. Disabled
notifications and unavailable/expired identity state block delivery.
