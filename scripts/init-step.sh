#!/bin/sh
set -eu
[ "$#" = 2 ] || { echo 'usage: init-step.sh runtime ca-hostname' >&2; exit 1; }
root=$(cd "$1" && pwd); host=$2
printf '%s' "$host" | grep -Eq '^[a-zA-Z0-9.-]+$' || exit 1
[ ! -e "$root/step/config/ca.json" ] || { echo 'CA already exists; refusing key replacement' >&2; exit 1; }
mkdir -p "$root/step/secrets" "$root/step/templates"
chmod 700 "$root/step" "$root/step/secrets"
python3 - "$root/step/secrets/password" <<'PY'
import secrets,sys,os
p=sys.argv[1]
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(48))
PY
docker run --rm --user 0:0 -v "$root/step:/home/step" --entrypoint step smallstep/step-ca:0.30.2@sha256:a2b17872915c193259b75a5474c398326f41bd199f0842093e52cf4182bc8270 \
 ca init --name 'Personal Access' --dns "$host" --address :9000 --provisioner bootstrap \
 --password-file /home/step/secrets/password --ssh
cp ssh/user.tpl "$root/step/templates/user.tpl"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);creds=json.loads((root/'credentials.json').read_text());p=root/'step/config/ca.json';c=json.loads(p.read_text())
c['db']={'type':'bbolt','dataSource':'/home/step/db/step.db'}
# Default structured error logs include the bearer OTT; common format omits it.
c['logger']={'format':'common'}
c['authority']['backdate']='0s'
c['authority']['provisioners']=[{
 'type':'OIDC','name':'personal','clientID':creds['clients']['ssh']['id'],
 'clientSecret':creds['clients']['ssh']['secret'],'configurationEndpoint':creds['issuer']+'/.well-known/openid-configuration',
 'listenAddress':'127.0.0.1:10000','claims':{'enableSSHCA':True,'disableRenewal':True,
   'minUserSSHCertDuration':'5m','maxUserSSHCertDuration':'1h','defaultUserSSHCertDuration':'1h'},
 'options':{'ssh':{'templateFile':'/home/step/templates/user.tpl'}}}]
p.write_text(json.dumps(c,indent=2));p.chmod(0o600)
(root/'step/db').mkdir(exist_ok=True)
PY
# Use the image's non-root step UID; no global host account changes.
docker run --rm --user 0:0 -v "$root/step:/home/step" --entrypoint sh smallstep/step-ca:0.30.2 -c 'chown -R step:step /home/step'
echo 'CA initialized. Keep the root key offline after backing it up. Do not publish before testing grants.'
