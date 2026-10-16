#!/usr/bin/env python3
"""Consistent encrypted backup. Call during a maintenance window.

The selected Compose services are stopped for the full snapshot, including
step-ca's embedded DB. Restarts run even on encryption failure. Decryption keys
are NEVER present in this script or on the source host.
"""
import argparse,datetime,os,re,subprocess,tarfile,tempfile
from pathlib import Path

def run(*args,**kwargs):return subprocess.run(args,check=True,**kwargs)
def backup(project,destination,recipient):
    project=project.resolve();destination=destination.resolve()
    if not (project/'runtime').is_dir():raise ValueError('Missing runtime')
    destination.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not recipient.startswith('age1'):raise ValueError('Use an age public recipient')
    status=subprocess.check_output(['docker','compose','--profile','ssh','ps','--services','--status','running'],cwd=project,universal_newlines=True).split()
    services=[s for s in status if s in ('casdoor','step-ca')]
    if not services:raise RuntimeError('No running identity service; check maintenance state')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=destination/(stamp+'.tar.age');partial=target.with_suffix('.partial')
    old=os.umask(0o077)
    try:
        run('docker','compose','--profile','ssh','stop',*services,cwd=project)
        try:
            with tempfile.TemporaryDirectory(prefix='identity-backup-') as tmp:
                archive=Path(tmp)/'snapshot.tar'
                with tarfile.open(archive,'w') as tar:
                    tar.add(project/'runtime',arcname='runtime')
                    tar.add(project/'compose.yaml',arcname='compose.yaml')
                run('age','-r',recipient,'-o',str(partial),str(archive))
                partial.replace(target)
        finally:run('docker','compose','--profile','ssh','start',*services,cwd=project)
    finally:os.umask(old)
    return target

def retain(directory):
    # Newest seven UTC days plus newest backup in each of four ISO weeks.
    files=sorted(directory.glob('????????T??????Z.tar.age'),reverse=True)
    daily={};weekly={}
    for f in files:
        dt=datetime.datetime.strptime(f.name[:16],'%Y%m%dT%H%M%SZ')
        daily.setdefault(dt.date(),f);weekly.setdefault(dt.isocalendar()[:2],f)
    keep=set(list(daily.values())[:7])|set(list(weekly.values())[:4])
    for f in files:
        if f not in keep:f.unlink()

def validate_remote(remote):
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*@[A-Za-z0-9.-]+:/[A-Za-z0-9_./-]+/', remote):
        raise ValueError('Use user@host:/absolute/dedicated-directory/')

def copy_retained(directory, remote):
    # Only timestamped ciphertext names can be transferred or removed.
    # The destination must be dedicated to this backup set.
    validate_remote(remote)
    run('rsync','-a','--delete','--include=????????T??????Z.tar.age',
        '--exclude=*','--',str(directory.resolve())+'/',remote)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path('.'));p.add_argument('--destination',type=Path,required=True);p.add_argument('--recipient',required=True);p.add_argument('--remote',help='rsync destination, e.g. backup@secondary:/srv/identity-backups/');a=p.parse_args()
    if a.remote:validate_remote(a.remote)
    target=backup(a.project,a.destination,a.recipient)
    if a.remote:run('rsync','-a','--',str(target),a.remote)
    # Do not delete older local backups until off-site copy succeeded.
    retain(a.destination)
    if a.remote:copy_retained(a.destination,a.remote)
    print(target.name)
