#!/usr/bin/env python3 
import os
import sys
import re
import numpy as np
import requests
from bs4 import BeautifulSoup, Tag, NavigableString

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

verbose = False

projcode = 'LT14_004'
#projcode = 'LT10_010'

workdir = '/data2/wwilliams/projects/lofar_obs/lt10_010'
workdir = '/home/wendy/projects/lofar_obs/lt10_010'
workdir = '/home/wendy/projects/lofar_obs/'+projcode.lower()


cdir = os.getcwd()

os.chdir(workdir)

args = sys.argv[1:]
if len(args) == 1:
    # specifying main id -- normal format is -4, 0, +6
    obsid = int(args[0].replace('L',''))
    obsids = [obsid+6, obsid, obsid-4]
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
targets = [data[selrobsids.index(obsid)][1] for obsid in obsids]
compls = [data[selrobsids.index(obsid)][3] for obsid in obsids]

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
The following message contains information regarding a LOFAR Cycle 10 project for which you are listed as the contact author. Please forward this information to the suitable individuals. <br>
<br>
We would like to inform you that an observation related to your LOFAR Cycle 10 project has been performed. Please find detailed information below:<br>
<br>
<b>General notes:</b> The inspection plots do not show non standard behaviour of stations over the whole observations. For all observations station dynamic spectra are available to help to establish the RFI and scintillation situation at station level.<br>
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
<br>
L<<ID1>> - <<TARGET1>><br>
<li>bright source(s) in sidelobes</li>
<li>RS406, RS409 strong DAB interference</li>
<br>
L<<ID2>> - <<TARGET2>><br>
<li>RS406, RS409 strong DAB interference</li>
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
emailbody = emailbody.replace('<<PID>>',projcode)
emailbody = emailbody.replace('<<<INSPECTTABLE>>>',inspecttabletxt)
emailbody = emailbody.replace('href="','href="https://proxy.lofar.eu/inspect/HTML/')


with open('L{i:d}-inspect.html'.format(i=obsid),'w') as f:
    f.write(emailbody)


urls.append('L{i:d}-inspect.html'.format(i=obsid))
#urls=['L{i:d}-inspect.html'.format(i=obsid)]

print('email body saved to inspect.html')

print('open these urls:')
print('\n'.join(urls))
s = input('y/(n)? ')

if not s.lower() == 'n':
    os.system('google-chrome '+' '.join(urls)+ ' &')


os.chdir(cdir)
