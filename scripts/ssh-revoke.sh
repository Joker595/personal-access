#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || exit 1
[ "$#" = 1 ] || { echo 'usage: ssh-revoke.sh linux-user' >&2; exit 1; }
printf '%s' "$1" | grep -Eq '^[a-z_][a-z0-9_-]*$' || exit 1
[ "$1" != root ] || exit 1
id "$1" >/dev/null
# Atomic empty file rejects all new certificate logins without changing sshd.
umask 077
temporary=$(mktemp /etc/ssh/personal-access/principals/.revoke.XXXXXX)
chmod 644 "$temporary"
mv "$temporary" "/etc/ssh/personal-access/principals/$1"
printf 'New certificate logins revoked. Existing sessions remain; inspect loginctl user-status %s and terminate explicitly if needed.\n' "$1"
