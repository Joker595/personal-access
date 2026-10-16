#!/usr/bin/env python3
"""Create private instance files once. Never print passwords or client secrets."""
import argparse,json,os,re,secrets
from pathlib import Path
from urllib.parse import urlsplit

def private(path,text):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open('x') as f:f.write(text)
    path.chmod(0o600)

def bootstrap(root,issuer,flightwatch,email):
    if any(urlsplit(x).scheme!='https' or not urlsplit(x).hostname or '\n' in x for x in (issuer,flightwatch)):
        raise ValueError('Use HTTPS origins')
    if not re.fullmatch(r'[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+',email):raise ValueError('Invalid owner email')
    if root.exists():raise ValueError('Runtime already exists; refusing to rotate identities or secrets')
    root.mkdir(parents=True,mode=0o700)
    (root/'casdoor/data').mkdir(parents=True,mode=0o700)
    admin_password=secrets.token_urlsafe(32);owner_password=secrets.token_urlsafe(32)
    clients={name:{'id':secrets.token_urlsafe(18),'secret':secrets.token_urlsafe(32)} for name in ('flightwatch-web','flightwatch-cli','ssh')}
    account=[{'name':name,'visible':True,'viewRule':'Self','modifyRule':rule} for name,rule in [
      ('ID','Immutable'),('Name','Admin'),('Display name','Self'),('Password','Self'),('Email','Self'),
      ('Tag','Admin'),('Is admin','Admin'),('Is forbidden','Admin'),('Is deleted','Admin'),
      ('WebAuthn credentials','Self'),('Multi-factor authentication','Self')]]
    org={'owner':'admin','name':'personal','displayName':'Personal','passwordType':'bcrypt',
         'passwordOptions':['AtLeast12','UpperCase','LowerCase','Digit'],
         'defaultTokenFormat':'JWT-Standard','useEmailAsUsername':True,'isProfilePublic':False,
         'accountItems':account,'countryCodes':['CN'],'languages':['zh','en'],'dcrPolicy':'disabled'}
    methods=[{'name':'Password','rule':'All'},{'name':'WebAuthn','rule':'All'}]
    apps=[]
    for name,client in clients.items():
        a={'owner':'admin','name':name,'displayName':name,'organization':'personal','cert':'cert-built-in',
           'clientId':client['id'],'clientSecret':client['secret'],'enablePassword':True,
           'enableSignUp':False,'enableSigninSession':True,'tokenFormat':'JWT-Standard',
           'expireInHours':1,'refreshExpireInHours':12,'signinMethods':methods.copy(),
           'grantTypes':['authorization_code'],'redirectUris':[],
           'tags':['app:ssh' if name=='ssh' else 'app:flightwatch']}
        if name=='flightwatch-web':a['redirectUris']=[flightwatch+'/auth/callback']
        elif name=='flightwatch-cli':
            a['grantTypes']=['urn:ietf:params:oauth:grant-type:device_code','refresh_token'];a['signinMethods'] += [{'name':'Device login','rule':'All'}]
        else:a['redirectUris']=['http://127.0.0.1:10000']
        apps.append(a)
    # Merge only explicitly defined fields on built-in application; close registration.
    apps.append({'owner':'admin','name':'app-built-in','enableSignUp':False})
    initial={'organizations':[org],'applications':apps,'users':[{
        'owner':'personal','name':email,'displayName':'Owner','email':email,'emailVerified':False,
        'password':owner_password,'isAdmin':False,'tag':'app:flightwatch,flightwatch-admin,app:ssh',
        'type':'normal-user','signupApplication':'flightwatch-web'}]}
    private(root/'casdoor/init.json',json.dumps(initial,indent=2))
    config=f'''appname = casdoor
httpport = 8000
runmode = prod
copyrequestbody = true
driverName = sqlite
dataSourceName = file:/data/casdoor.db?cache=shared
 dbName = casdoor
showSql = false
origin = {issuer}
isDemoMode = false
showGithubCorner = false
enableErrorMask = true
logPostOnly = true
defaultLanguage = zh
initAdminPassword = {admin_password}
initDataFile = /conf/init.json
initDataMerge = true
initDataNewOnly = true
logConfig = {{"adapter":"console"}}
'''.replace('\n dbName','\ndbName')
    private(root/'casdoor/app.conf',config)
    private(root/'credentials.json',json.dumps({'issuer':issuer,'owner_email':email,
        'admin_password':admin_password,'owner_initial_password':owner_password,'clients':clients},indent=2))
    private(root/'flightwatch-client-secret',clients['flightwatch-web']['secret'])
    private(root/'flightwatch.env',f'''FLIGHTWATCH_OIDC_ISSUER={issuer}
FLIGHTWATCH_OIDC_CLIENT_ID={clients['flightwatch-web']['id']}
FLIGHTWATCH_OIDC_CLI_CLIENT_ID={clients['flightwatch-cli']['id']}
FLIGHTWATCH_OIDC_ORGANIZATION=personal
FLIGHTWATCH_OIDC_CLIENT_SECRET_FILE=/data/oidc-client-secret
FLIGHTWATCH_PUBLIC_URL={flightwatch}
FLIGHTWATCH_SEED_DEMO=0
''')
    print('Private runtime generated. Set container UID ownership before starting. Credentials remain in runtime/credentials.json.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,default=Path('runtime'));p.add_argument('--issuer',required=True);p.add_argument('--flightwatch',required=True);p.add_argument('--owner-email',required=True)
    a=p.parse_args();bootstrap(a.runtime,a.issuer.rstrip('/'),a.flightwatch.rstrip('/'),a.owner_email)
