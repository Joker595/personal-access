# Deployment and acceptance

This repository is an implementation under validation, not a claim that every
client or production host has passed acceptance. See VALIDATION.md.

## Initialize

Requires Docker Compose, Python 3.12+, age, rsync and OpenSSH. Use a dedicated
checkout owned by the administrator. Do not use a public web directory.

```sh
python3 scripts/bootstrap.py --issuer https://id.example.com \
  --flightwatch https://flights.example.com --owner-email you@example.com
```

`runtime/credentials.json` contains random initial passwords and confidential
client secrets. Keep mode 0600. TUI receives only its public client ID. Casdoor application client credentials
permit privileged organization API access: restrict their files to the backend
service, never expose them to browser or TUI code, and rotate them after a leak.
Create users through the administrator UI; open signup is disabled. Account IDs
are generated once by Casdoor, not from email. Grant `app:flightwatch` and
`app:ssh` separately. Grant `flightwatch-admin` only to global service managers.
The bootstrap owner receives these explicit grants. Other new users receive none.

Before starting, set runtime/casdoor/data ownership to the `casdoor` UID from the
pinned image. Container configuration files must also be readable by that UID;
do not make credential files world-readable. Start only the loopback-bound
Casdoor service. After initialization, stop it, seal bootstrap, then restart:

```sh
docker compose up -d casdoor
docker compose stop casdoor
python3 scripts/seal-bootstrap.py runtime
docker compose up -d casdoor
```

Seal verifies registration is closed and removes import/password directives.
Never re-import the bootstrap file into a live database: doing so can restore
initial permissions. Test that restart preserves the exact subject in owner.json.
The initial owner email is UNVERIFIED: verify through a working SMTP provider or
an administrator-controlled ownership check before enabling notifications.

## HTTPS and an existing edge

Copy config/nginx.conf.template to runtime/nginx.conf, replace the hostname,
and install fullchain.pem/privkey.pem into runtime/tls. Use the `edge` profile
only when ports 80/443 are available. Renew certificates with the host's existing
ACME facility; reload Nginx only after `nginx -t` succeeds.

With an existing Caddy/Nginx edge, leave the edge profile disabled. Connect the
existing edge and Casdoor to a dedicated network, proxy only the chosen identity
hostname to casdoor:8000, and overwrite forwarded headers. Do not expose port
8000 publicly. Apply equivalent request and verification-code rate limiting.
Do not enable proxy request-body logging. Disable query-string logging on auth
routes: authorization codes and tokens must not enter audit logs.

For mainland China, verify both the domain's ICP record and its Alibaba Cloud
access filing before publishing. A wildcard DNS record alone is not evidence.

## SSH

Run scripts/init-step.sh runtime ca.example.com, then start the `ssh` profile.
Trust the CA root fingerprint through an independent channel. Publish CA HTTPS
on a dedicated hostname, preserving end-to-end certificate validation. The CA
root private key should be removed from the online host after offline backup;
keep the intermediate and SSH signing keys in the restricted runtime directory.

Install the public user CA key and ssh/50-personal-access.conf on each host.
Check existing AllowUsers/AllowGroups and include the individually created
Linux users. Never add the emergency account to identity-managed. Use
scripts/ssh-grant.sh USER SUBJECT per host. sudo is separate and never granted
by this script. A grant maps only this CA's issuer to a subject; never mix issuers
under one SSH CA without an issuer-qualified principal migration.

Keep an emergency session open. Run `sshd -t`, inspect `sshd -T -C user=USER`,
reload, and verify a NEW certificate-authenticated connection before tightening
existing authentication. Test unauthorized principal, root, host certificate,
expired and >1h certificate requests. Port forwarding remains allowed for
VS Code Remote; agent and X11 forwarding are not included in issued certificates.

On Mac/Windows install official `step`, bootstrap CA with a pinned fingerprint,
then `step ssh login --provisioner personal you@example.com`. SSH/SCP/VS Code use
the local agent. Certificates have a maximum one-hour validity interval; expiry
does not kill existing sessions. The CA explicitly sets backdate=0s; synchronize
host clocks. Its common log formatter excludes OTT/token/body fields, unlike
the default structured error logger. Never put credentials in CA URL queries. For immediate revocation remove server grants
and explicitly terminate existing sessions if required. Browser/device/passkey
revocation does not invalidate certificates already issued.

## Backup and recovery

Daily run scripts/backup.py with the offline age public recipient and an SSH
remote destination on the other server. It stops only identity writers while
copying all runtime data (SQLite, CA embedded DB, config and signing keys), then
restarts them even when encryption fails. Seven daily plus four weekly snapshots
are retained locally and remotely. The remote path must be a dedicated backup
directory: timestamped ciphertext files outside the retention set are removed
only after the new backup has been copied successfully; unrelated files survive.
The decryption key must remain offline. Install config/personal-access-backup.service
and .timer in /etc/systemd/system; create /etc/personal-access/backup.env (0600)
with BACKUP_RECIPIENT=age1... and BACKUP_REMOTE=backup@secondary:/srv/identity-backups/.
Pin the remote SSH host key and use an account restricted to that directory.
Check the Python and age paths for the host, run the service once and verify the
off-site file, then enable the timer. Do not install the timer before these checks.

Restore into a new directory with scripts/restore.py. Verify SQLite integrity,
owner subjects, CA fingerprints and file ownership; start isolated services and
perform login/signing tests before switching DNS. A restore drill is mandatory;
merely producing an encrypted archive is not proof of recoverability.

## Recovery and audit

An administrator recovers lost account credentials in Casdoor. Preserve user ID;
never delete/recreate a user merely to change email. Password and passkey
credentials attach to that same user. Synced passkeys identify credentials,
not individual physical iPhones/Macs/Windows devices. Record credential grants
and revocations without private keys, passwords, access or refresh tokens.
