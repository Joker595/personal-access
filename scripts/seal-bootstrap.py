#!/usr/bin/env python3
"""Run once with Casdoor STOPPED, before publishing any network ingress."""
import argparse,json,sqlite3,os
from pathlib import Path

def seal(root):
    path=root/'casdoor/data/casdoor.db'
    if not path.is_file():raise ValueError('Database must be initialized first')
    with sqlite3.connect(str(path)) as db:
        db.execute('BEGIN IMMEDIATE')
        # Match verified v4.20.0 schema. Abort if schema differs.
        db.execute('UPDATE application SET enable_sign_up=0 WHERE owner=? AND name=?',('admin','app-built-in'))
        for row in db.execute('SELECT owner,name,enable_sign_up FROM application'):
            if row[2]:raise ValueError('Open registration remains enabled: '+row[1])
        expected=json.loads((root/'credentials.json').read_text())['owner_email']
        users=db.execute('SELECT id,email FROM user WHERE owner=? AND name=?',('personal',expected)).fetchall()
        if len(users)!=1:raise ValueError('Explicit owner does not match initialized identity')
        if not users:raise ValueError('Missing explicit owner')
    conf=root/'casdoor/app.conf';text=conf.read_text()
    lines=[line for line in text.splitlines() if not line.startswith(('initAdminPassword =','initDataFile ='))]
    lines.append('initDataFile = ""')
    tmp=conf.with_suffix('.tmp');tmp.write_text('\n'.join(lines)+'\n');tmp.chmod(0o600);tmp.replace(conf)
    owner=root/'owner.json'
    owner.write_text(json.dumps({'issuer':json.loads((root/'credentials.json').read_text())['issuer'],'subject':users[0][0],'email':users[0][1]},indent=2));owner.chmod(0o600)
    print('Bootstrap sealed; immutable owner saved privately in runtime/owner.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('runtime',type=Path);a=p.parse_args();seal(a.runtime)
