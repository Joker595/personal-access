#!/bin/sh
# Root-only mapping of an OIDC UUID subject to one existing Linux account.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run as root' >&2; exit 1; }
[ "$#" = 2 ] || { echo 'usage: ssh-grant.sh linux-user immutable-subject' >&2; exit 1; }
user=$1; subject=$2
printf '%s' "$user" | grep -Eq '^[a-z_][a-z0-9_-]*$' || exit 1
printf '%s' "$subject" | grep -Eq '^[a-zA-Z0-9_-]+$' || exit 1
[ "$user" != root ] || { echo 'Root grants are forbidden' >&2; exit 1; }
id "$user" >/dev/null
getent group identity-managed >/dev/null || groupadd identity-managed
usermod -aG identity-managed "$user"
install -d -m 755 /etc/ssh/personal-access/principals
umask 077
temporary=$(mktemp /etc/ssh/personal-access/principals/.grant.XXXXXX)
printf '%s\n' "$subject" > "$temporary"
chown root:root "$temporary"
chmod 644 "$temporary"
mv "$temporary" "/etc/ssh/personal-access/principals/$user"
sshd -t
printf 'Grant installed for %s; sudo is unchanged. Verify a new SSH session.\n' "$user"
