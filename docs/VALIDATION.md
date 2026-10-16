# Validation record

As of 2026-10-16:

- Confirmed official Casdoor v4.20.0 and step-ca v0.30.2 release pages; pinned
  Docker multiarch manifest digests. Casdoor Docker tag omits the Git tag's `v`.
- Casdoor SQLite initialized in an isolated loopback container.
- Actual password authorization-code flow, S256 PKCE exchange and nonce checked.
- Actual device authorization, browser-equivalent approval, token issuance and
  introspection tested. Both flows yielded the same UUID subject.
- Important correction: persisted Casdoor grantTypes use protocol values
  `authorization_code`, `urn:ietf:params:oauth:grant-type:device_code`,
  `refresh_token`; UI labels such as “Device Code” are not stored values.
- Bootstrap sealing closes built-in signup and disables re-import. Same subject
  observed after restart.
- Actual OIDC ID token to step-ca SSH user certificate signing passed over
  verified test TLS. Native OpenSSH accepted the authorized UUID/account and
  rejected a different principal, an expired certificate and the root account.
  Requests for two-hour validity were rejected by the CA. With backdate=0s,
  the actual validity interval was exactly 3,600 seconds.
- The default step-ca error logger included the OTT. Set common format and
  confirmed no OTT/JWT appeared in subsequent signing logs.
- Two ordinary users, an application administrator and an ungranted test user
  were created in isolated Casdoor. Flightwatch login grants worked; missing
  application grants and all missing SSH grants were rejected.
- Nginx updated to 1.30.6 and pinned by digest after checking official advisories.
- Consistent stopped Casdoor/CA snapshot encrypted with age and restored into
  a new directory. SQLite integrity, UUID subject and CA public/private material
  matched. Off-site transfer and production recovery drill remain pending.
- Flightwatch regression and new isolation/quota/migration tests passed locally
  (109 tests before the final additional migration-lock tests).
  Production data has NOT been migrated by this record.

Pending: production identity hostname and ICP access check, invitation/passkey/
optional SMTP delivery, two-user and administrator live acceptance, SSH host
integration and expiry checks, backup copy/restore drill, iPhone/Mac/Windows
interaction. Do not present these pending checks as completed.

Primary references:
- https://github.com/casdoor/casdoor/releases/tag/v4.20.0
- https://github.com/smallstep/certificates/releases/tag/v0.30.2
- https://casdoor.ai/docs/how-to-connect/oauth/#device-grant
- https://smallstep.com/docs/step-ca/templates/

- https://nginx.org/en/security_advisories.html
- https://github.com/smallstep/certificates/blob/v0.30.2/logging/clf.go
