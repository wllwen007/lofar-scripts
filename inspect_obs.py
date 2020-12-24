#!/usr/bin/env python3 
import os
import sys
import re
import pwd
import numpy as np
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import datetime
import urllib3
import keyring
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

verbose = False

cycle = 14
projcode = 'LT14_004'
#projcode = 'LT14_003'  # deep
if projcode == 'LT14_004':
    rohd = 2516
elif projcode == 'LT14_003':
    rohd = 2515
#projcode = 'LT10_010'

workdir = '/data2/wwilliams/projects/lofar_obs/lt10_010'
workdir = '/home/wendy/projects/lofar_obs/lt10_010'
workdir = '/home/wendy/projects/lofar_obs/'+projcode.lower()

idm = 4
idp = 6

idm = 2
idp = 2

cdir = os.getcwd()

os.chdir(workdir)


def get_obsid(P,d,matchpartial=False):
    
    print('Looking up obsid for',P,d)
    
    r = requests.get('https://proxy.lofar.eu/inspect/HTML/fullindex.html', verify=False)
    inspecttablehtml = r.text


    soup = BeautifulSoup(inspecttablehtml, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')

    header = rows[0]
    rows = rows[1:]

    data = []
    selind = []
    selrows = []
    selrobsids = []
    for irow, row in enumerate(rows):
        cols = row.find_all('td')
        rh = row.find('th')
        robsid = int(rh.text.strip().replace('L',''))
        #if robsid not in obsids:
            #continue
        #if 'LT10_010' not in cols[0].text:
        if projcode not in cols[0].text:
            continue
        cols = [ele.text.strip() for ele in cols]
        data.append([robsid]+[ele for ele in cols if ele]) 
        selind.append(irow)
        selrows.append(row)
        selrobsids.append(robsid)
        
    data = np.array(data)
    
    # match the observation name
    if not matchpartial:
        data_pind = (data[:,2] == P)
        if np.sum(data_pind) == 0:
            print ('Observation',P,'does not exist')
            sys.exit(1)
    else:
        
        data_pind = [P in d for d in data[:,2] ]
        if np.sum(data_pind) == 0:
            print ('Observation',P,'does not exist')
            sys.exit(1)
    
    data = data[data_pind,:]
    
    # match the date
    dates = data[:,8]
    dates = np.array([d[0:10].replace('-','') for d in dates])
    dates_ind = (dates == d)
    print (dates_ind)
    if sum(dates_ind) != 1:
        if sum(dates_ind) > 1:
            print('more than 1 dates match')
            print(dates[dates_ind])
            print(data[dates_ind])
        else:
            print('no dates match')
            print(data)
            sys.exit(1) 
    
    
    obsid = int(data[dates_ind,0][0])

    print('Found obsid:', obsid)
    
    return obsid

momcode = ''

args = sys.argv[1:]
if len(args) == 1:
    # we're specifying a pointing/date and need to look up the obsid
    if 'P' in args[0]:
        rep = ''
        if 'REP' in args[0]:
            args[0] = args[0].replace('REP','')
            rep = 'REP'
        # P000+03P000+08_120200623  ... copy past has this format
        if '_' in args[0]:
            C = args[0][0:16]
            Cd = args[0][16:]
            p = C[0:C.index('_')]
        # P000+03P000+08_120200623  ... copy past has this format
        else:
            C = args[0][0:14]
            Cd = args[0][14:]
            p = C[0:14]
        p1 = p[0:4]
        p2 = p[7:11]
        
        P = p1+p2+'REF'
        
        obsid = get_obsid(P,Cd)
        
        momcode = C+rep
        
        obsids = [obsid+idp, obsid, obsid-idm]
        
    # special case for deep observations
    elif ('ELAIS' in args[0]) :
        
        rep = ''
        if 'REP' in args[0]:
            args[0] = args[0].replace('REP','')
            rep = 'REP'
        # ELAIS-RUN1-2020111220201112
        C = args[0][0:19]
        Cd = args[0][19:]
        P = 'ELAIS-N1'
        obsid = get_obsid(P,Cd, matchpartial=True)
        obsids = [obsid+idp, obsid, obsid-idm]
        
        
    # special case for deep observations
    elif  ('Lockman' in args[0]):
        
        rep = ''
        if 'REP' in args[0]:
            args[0] = args[0].replace('REP','')
            rep = 'REP'
        # ELAIS-RUN1-2020111220201112
        C = args[0][0:9]
        Cd = args[0][10:]
        print(C,Cd)
        
        P = args[0].split('_')[0]
        obsid = get_obsid(P,Cd, matchpartial=True)
        obsids = [obsid+idp, obsid, obsid-idm]
        
    # we're specifying an obs id
    elif 'L' in args[0]:
        # specifying main id -- normal format is -4, 0, +6
        obsid = int(args[0].replace('L',''))
        obsids = [obsid+idp, obsid, obsid-idm]
    # we're specifying an obs id without the L
    else:
        # specifying main id -- normal format is -4, 0, +6
        obsid = int(args[0])
        obsids = [obsid+idp, obsid, obsid-idm]
    
    
    
elif len(args) == 3:
    # specify all 3 obsids if something is different
    obsids = [int(arg.replace('L','')) for arg in args]
else:
    print("invalid arguments")
    sys.exit(1)


print(obsids)


sobsids = [str(obsid) for obsid in obsids]

assert len(sobsids[0]) == len(sobsids[1])
assert len(sobsids[2]) == len(sobsids[1])
tsel = np.ones(len(sobsids[0]),dtype=bool)
for i in range(len(tsel)):
    if (sobsids[0][i] == sobsids[1][i]) and (sobsids[2][i] == sobsids[1][i]):
        tsel[i] = 0
sobsids = [''.join(np.array([c for c in sobsids[0]])[tsel]),
           ''.join(np.array([c for c in sobsids[1]])[tsel]),
           sobsids[2]]
        

#os.system('rm -rf fullindex.html')
#os.system('wget --no-check-certificate https://proxy.lofar.eu/inspect/HTML/fullindex.html')
#with open('fullindex.html','r') as f:
    #inspecttablehtml = f.readlines()
#inspecttablehtml = ' '.join(inspecttablehtml)
r = requests.get('https://proxy.lofar.eu/inspect/HTML/fullindex.html', verify=False)
inspecttablehtml = r.text


soup = BeautifulSoup(inspecttablehtml, 'html.parser')
table = soup.find('table')
rows = table.find_all('tr')

header = rows[0]
rows = rows[1:]

data = []
selind = []
selrows = []
selrobsids = []
for irow, row in enumerate(rows):
    cols = row.find_all('td')
    rh = row.find('th')
    robsid = int(rh.text.strip().replace('L',''))
    if robsid not in obsids:
        continue
    #if 'LT10_010' not in cols[0].text:
    if projcode not in cols[0].text:
        continue
    cols = [ele.text.strip() for ele in cols]
    data.append([ele for ele in cols if ele]) 
    selind.append(irow)
    selrows.append(row)
    selrobsids.append(robsid)

inspecttable = selrows
inspecttable.insert(0, header)


inspecttabletxt = ''
for row in inspecttable:
    inspecttabletxt += str(row)+'\n'


# match the target names to the obsids
present = np.array([ obsid in selrobsids for obsid in obsids])
obsids = [ obsid for obsid in obsids if obsid in selrobsids ]
target_missing = ~np.all(present)
targets = []
compls = []
for obsid in obsids:
    if obsid in selrobsids:
        targets.append(data[selrobsids.index(obsid)][1])
        compls.append(data[selrobsids.index(obsid)][3])
    

# get list of urls to open
## some random subbands
urls = []
i = 1
for obsid in obsids:
    if i == 1:
        i = 0
    else:
        i = 1
    urls.append("https://proxy.lofar.eu/inspect/HTML/{id:d}/Stations/station_beamlets.html".format(id=obsid))
    urls.append('https://proxy.lofar.eu/inspect/HTML/{id:d}/SBpages/SAP00{i:d}_SB019.html'.format(id=obsid, i=i))
    urls.append('https://proxy.lofar.eu/inspect/HTML/{id:d}/SBpages/SAP00{i:d}_SB119.html'.format(id=obsid, i=i))

# check the cobalt logs
for obsid in obsids:
    r = requests.get("https://proxy.lofar.eu/inspect/{id:d}/rtcp-{id:d}.errors".format(id=obsid), verify=False)
    cobaltlog = r.text.strip()
    
    print('###' , obsid, )
    print('- cobalt error log length', len(cobaltlog), )
    if verbose:
        print(cobaltlog)
    elif len(cobaltlog) > 4400:
        print('this is a longer cobalt log: (will add log to url list to open)')
        #print(cobaltlog)
        urls.append("https://proxy.lofar.eu/inspect/{id:d}/rtcp-{id:d}.errors".format(id=obsid))
    else:
        print('<OK>')

print()

# check the observation page - input data losses
for obsid in obsids:
    
    print('###' , obsid, )
    obsurl = "https://proxy.lofar.eu/inspect/HTML/{id:d}/index.html".format(id=obsid)
    r = requests.get(obsurl, verify=False)
    obslog = r.text.strip()
    
    try:
        soup = BeautifulSoup(obslog, 'html.parser')
        nextNode = soup.find('h3', text=re.compile('Input loss report'))
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                break
            if isinstance(nextNode, Tag):
                if nextNode.name == "h3":
                    break
            if isinstance(nextNode, NavigableString):
                continue
            rows = nextNode.find_all('tr')
            if len(rows) > 1:
                table = nextNode
                
        print('- ',len(rows), 'stations with minor input data losses <OK>')
        

        checkloss = False
        for row in rows:
            rh = row.find('th').text
            
            rc = float(row.find('td').text.strip().replace('%',''))
            if verbose:
                print(rh, rc)
            elif rc > 1.0:
                print(rh, rc)
                checkloss = True
        if checkloss:
            print('some high input data losses <!!>')
                
    except:
        print("Something is wrong with this page (will add it to list to open):", obsurl)
        urls.append(obsurl)
            
            
            

print()

# check the bst page - no data
for obsid in obsids:
    
    print('###' , obsid, )
    r = requests.get("https://proxy.lofar.eu/inspect/HTML/{id:d}/Stations/station_beamlets.html".format(id=obsid), verify=False)
    bst = r.text.strip()
    
    soup = BeautifulSoup(bst, 'html.parser')

    data = []

    rows = soup.find_all('tr')


    for irow, row in enumerate(rows):
        cols = row.find_all('td')
        rh = row.find('th')
        cols = [ele.text.strip() for ele in cols]
        #data.append([ele for ele in cols if ele]) 
        data.append(cols)



    missingdata = False
    missing = []
    for i in range(len(data)):
        if len(data[i]) > 0:
            if 'NO DATA' in data[i][0]:
                missing.append(data[i-1][0])
                missingdata = True
    missing = np.unique(missing)
    if missingdata:
        print('some data missing <!!>')
        print(len(missing), 'station(s) with NO DATA: ',','.join(missing))
    else:
        print()

print()

# generate the email body

emailbody = r'''<html>
  <head>
    <style type="text/css">
      * {
        font-family: Sans-Serif;
        font-size: Small;
        p {
  margin-bottom: 0px; 
  margin-top: 0px; 
  }
      }
    </style>
  </head>
<base href="" />
<body>
<b><<PID>>: observations L<<SID2>>/<<SID1>>/<<SID0>> successful</b><br>
<br>
Dear Colleague <br>
<br>
The following message contains information regarding a LOFAR Cycle <<CYCLE>> project for which you are listed as the contact author. Please forward this information to the suitable individuals. <br>
<br>
We would like to inform you that an observation related to your LOFAR Cycle <<CYCLE>> project has been performed. Please find detailed information below:<br>
<br>
<b>General notes:</b> The inspection plots do not show non standard behaviour of stations over the whole observations. For all observations station dynamic spectra are available to help to establish the RFI and scintillation situation at station level.<br>
<<<MISSING>>>
<<<OBSCOMMENT>>>
<br>
<b>Observations:</b> <br>
        <table>
<<<INSPECTTABLE>>>
        </table>
<br>
Performance of the system: Completeness of data recorded was <<COMPL0>>, <<COMPL1>>, and <<COMPL2>> for <<TARGET0>>, main, and <<TARGET2>> runs, respectively. <br>
<br>
L<<ID0>> - <<TARGET0>><br>
<li>RS406, RS409 strong DAB interference</li>
<<COMMENT0>>
<br>
L<<ID1>> - <<TARGET1>><br>
<li>bright source(s) in sidelobes</li>
<li>RS406, RS409 strong DAB interference</li>
<<COMMENT1>>
<br>
L<<ID2>> - <<TARGET2>><br>
<li>RS406, RS409 strong DAB interference</li>
<<COMMENT2>>
<br>
<b>Data processing:</b> completed<br>
<br>
<b>Archiving:</b> processed data will be ingested into the LTA.<br>
<br>
<b>Remarks:</b> Please analyse the validation plots at <a href="">https://proxy.lofar.eu/inspect/HTML/</a> within 24 hours after this notification and submit a support request at <a href="https://support.astron.nl/rohelpdesk">https://support.astron.nl/rohelpdesk</a> in case you need to report problems about their quality. After this time window has passed, we will assume that your judgement is that the observation was successful and we will complete the actions described above to support your run.<br>
<br>
From the moment the data are made available to you at the LTA you have four weeks to check their quality and to report any problems to the Observatory. After this time window has passed, no requests for re-observation will be considered.<br>
<br>
<b>Actions:</b> If you need any further clarification, please do not hesitate to contact us through the RO helpdesk at <a href="https://support.astron.nl/rohelpdesk">https://support.astron.nl/rohelpdesk</a> , specifying your project code in the subject.<br>
<br>
<br>
Best regards,<br>
Wendy Williams<br>
<br>
expert user support<br>
</body>
</html>

'''

for i, obsid in enumerate(obsids):
    emailbody = emailbody.replace('<<ID{i:d}>>'.format(i=i), str(obsid))
    emailbody = emailbody.replace('<<SID{i:d}>>'.format(i=i), str(sobsids[i]))
    emailbody = emailbody.replace('<<COMPL{i:d}>>'.format(i=i), str(compls[i]))
    emailbody = emailbody.replace('<<TARGET{i:d}>>'.format(i=i), str(targets[i]))
if target_missing:
    emailbody = emailbody.replace('<<<MISSING>>>', 'NOTE: one calibrator observation is missing but the target and one calibrator is present.<br>')
else:
    emailbody = emailbody.replace('<<<MISSING>>>','')
emailbody = emailbody.replace('<<PID>>',projcode)
emailbody = emailbody.replace('<<CYCLE>>',str(cycle))
emailbody = emailbody.replace('<<<INSPECTTABLE>>>',inspecttabletxt)
emailbody = emailbody.replace('href="','href="https://proxy.lofar.eu/inspect/HTML/')



print('open these urls:')
print('\n'.join(urls))
s = input('y/(n)? ')

if not s.lower() == 'n':
    os.system('google-chrome '+' '.join(urls)+ ' > /dev/null 2>&1 &')


# open email body to edit
with open('addcomments.tmp','w' ) as f:
    for i, obsid in enumerate(obsids):
        f.write('L'+str(obsid)+' - \n')
    f.write('general:\n')
os.system('vim addcomments.tmp'.format(i=obsid))


with open('addcomments.tmp','r' ) as f:
    lines = f.readlines()
comments = ['','','']
obscomment=''
for line in lines:
    C = line.strip()
    if 'general' in C:
        obscomment = C.replace('general:','').strip()
    else:
        i = obsids.index(int(C.split('-')[0].strip().replace('L','')))
        comment = C.split('-')[1].replace('-','').strip()
        if len(comment) > 0:
        
            comments[i] += '<li>{comment}</li>\n'.format(comment=comment)
    

if obscomment != '':
    emailbody = emailbody.replace('<<<OBSCOMMENT>>>', obscomment+'<br>')
else:
    emailbody = emailbody.replace('<<<OBSCOMMENT>>>','')
    
for i, obsid in enumerate(obsids):
    emailbody = emailbody.replace('<<COMMENT{i:d}>>'.format(i=i), comments[i])
    

with open('L{i:d}-inspect.html'.format(i=obsid),'w') as f:
    f.write(emailbody)
os.system('google-chrome '+'L{i:d}-inspect.html'.format(i=obsid)+ ' &')


#urls.append('L{i:d}-inspect.html'.format(i=obsid))
#urls=['L{i:d}-inspect.html'.format(i=obsid)]

print('email body saved to L{i:d}-inspect.html'.format(i=obsid))

print('Please ingest data',momcode)

print('send email:')
s = input('(y)/n? ')


if s.lower() != 'n':
    
    with open('L{i:d}-inspect.html'.format(i=obsid),'r') as  f:
        slines = f.readlines()
    

    msg = MIMEMultipart('alternative')
    # Record the MIME types of both parts - text/plain and text/html.
    #part1 = MIMEText(text, 'plain')
    part2 = MIMEText(emailbody, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    #msg.attach(part1)
    msg.attach(part2)
    
    username = keyring.get_password('PY_STRW_MAIL', 'user_key')
    pw = keyring.get_password('PY_STRW_MAIL', username) 
    user = pwd.getpwuid(os.getuid())[4].replace(',','')
    me = '{name} <{user}@strw.leidenuniv.nl>'.format(name=user,user=username)
    you = 'ro-helpdesk@astron.nl'
    msg['Subject'] = 'ROHD-{rohd} Project {proj}'.format(rohd=rohd, proj=projcode)
    msg['From'] = me
    msg['Date'] = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )
    msg['To'] = you
    with  smtplib.SMTP_SSL('smtp.strw.leidenuniv.nl', port=465) as s:
        s.login(username, pw)
        s.sendmail(me, [you], msg.as_string())
        
    print('Email sent')
    
    os.system('rm addcomments.tmp')
        

os.chdir(cdir)
