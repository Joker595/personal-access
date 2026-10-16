#!/usr/bin/env python3
"""Decrypt into a NEW directory; never overwrite a running deployment."""
import argparse,os,subprocess,tarfile,tempfile
from pathlib import Path

def restore(archive,key,destination):
    if destination.exists():raise ValueError('Destination must not exist')
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='identity-restore-') as temp:
        clear=Path(temp)/'snapshot.tar'
        subprocess.run(['age','-d','-i',str(key),'-o',str(clear),str(archive)],check=True)
        with tarfile.open(clear) as tar:
            for member in tar.getmembers():
                parts=Path(member.name).parts
                if member.name.startswith('/') or '..' in parts or member.issym() or member.islnk() or member.isdev():
                    raise ValueError('Unsafe backup member')
            destination.mkdir(mode=0o700,parents=True)
            tar.extractall(destination,filter='data')
    print('Restored offline. Verify data, CA fingerprints and DNS before starting services.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--key',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args();restore(a.archive,a.key,a.destination)
