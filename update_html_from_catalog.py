#!/usr/bin/env python3
"""Refresh both portable HTML files and the GitHub Pages entry point from the exported catalog."""
from pathlib import Path
import argparse,base64,hashlib,json,re

HERE=Path(__file__).resolve().parent
PHOTO_FIELDS=['imageData','imageOriginalData','imageCrop','imageOriginalWidth','imageOriginalHeight','imageContext','imageRemoved','imageFile','imageAlt','imageCredit','imageLicense','imageSource']

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('catalog',nargs='?',type=Path,default=HERE/'ACSP-Website-Catalog.json')
 p.add_argument('--html',nargs='+',type=Path,help='Explicit HTML targets; by default updates both supplied HTML files and index.html')
 args=p.parse_args();catalog=json.loads(args.catalog.read_text(encoding='utf-8'))
 assert catalog.get('schemaVersion')==3 and catalog.get('kind')=='catalog','Use the exported version 3 catalog.'
 rows=catalog['resources'];assert 0<len(rows)<=500,'Catalog must have 1–500 resources.'
 members=json.loads((HERE/'ACSP-Member-School-Reference.json').read_text(encoding='utf-8'))
 aliases=members['aliases'];full=set(members['fullMembers'])
 assert len({r['id'] for r in rows})==len(rows),'Duplicate IDs.'
 assert len({r['url'].rstrip('/') for r in rows})==len(rows),'Duplicate source URLs.'
 files=args.html or [HERE/'Planning-Knowledge-Hub-Resource-Collection.html',HERE/'20261101Planning-Knowledge-Hub-Updated.html']
 updates=[]
 fingerprint=hashlib.sha256(json.dumps(catalog,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:12]
 key='planning-hub-v3-acsp-journal-20261101-'+fingerprint
 represented={}
 for r in rows:
  if 'ai-in-planning' not in r.get('collectionIds',[]):continue
  university=aliases.get(r['institution'],r['institution'])
  assert university in full,f'Unknown ACSP Full Member university: {university}'
  for domain in r.get('domains',[]):
   pair=(domain,university)
   assert pair not in represented,f'One entry per school/category: {university} already has {represented.get(pair)} in {domain}; duplicate {r["id"]}'
   represented[pair]=r['id']
 for r in rows:
  if 'ai-in-planning' not in r.get('collectionIds',[]) or 'Research' not in r.get('domains',[]):continue
  assert r.get('resourceType')=='Publication',f'{r["id"]}: Research requires a published journal article.'
  assert re.fullmatch(r'Peer-reviewed journal article · .+',r.get('sourceStatus',''),re.I),f'{r["id"]}: record the peer-reviewed journal name in Source Status.'
  years=[int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b',r.get('date',''))]
  assert years and min(years)>=2021,f'{r["id"]}: Research must be published from 2021 onward.'
  from urllib.parse import urlsplit,unquote
  host=(urlsplit(r['url']).hostname or '').lower()
  assert host!='arxiv.org' and not host.endswith('.arxiv.org'),f'{r["id"]}: use the published journal source.'
  assert host!='mdpi.com' and not host.endswith('.mdpi.com') and not re.search(r'10\.3390(?:/|$|[?#])',unquote(r['url']).lower()) and 'mdpi' not in r.get('sourceStatus','').lower(),f'{r["id"]}: MDPI journals are excluded.'
 for file in files:
  text=file.read_text(encoding='utf-8');match=re.search(r'<script id="hub-data" type="application/json">(.*?)</script>',text,re.S)
  assert match,f'Missing hub-data: {file.name}'
  seed=json.loads(match.group(1));allowed=set(re.findall(r"'([^']+)'",re.search(r'const recordFields = (\[.*?\]);',text).group(1)))
  prepared=[];registry={}
  for original in rows:
   r={k:v for k,v in original.items() if k in allowed}
   r['institution']=aliases.get(r['institution'],r['institution'])
   assert r['institution'] in full,f"Unverified ACSP Full Member: {r['institution']}"
   assert r.get('imageFile') and r.get('imageAlt') and r.get('imageCredit') and r.get('imageLicense') and r.get('imageSource'),f"Missing cover metadata: {r['id']}"
   if 'Research' in r.get('domains',[]):assert 'figure' in r.get('imageContext','').lower(),f"Research needs an identified paper figure: {r['id']}"
   name=r['imageFile'];assert re.fullmatch(r'(?:photos/(?:teaching|research|applications)|figures/research)-[0-9]{2}\.jpg',name),f'Unsupported bundled cover: {name}'
   data=r.get('imageData')
   if not data:
    raw=(HERE/name).read_bytes();assert len(raw)<=80000,'Cover exceeds 80 KB.'
    data='data:image/jpeg;base64,'+base64.b64encode(raw).decode()
   assert re.fullmatch(r'data:image/(?:jpeg|png|webp);base64,[A-Za-z0-9+/]+=*',data) and len(data)<=150000,'Invalid or oversized image.'
   photo={k:r[k] for k in PHOTO_FIELDS if k in r};photo.update(id=r['id'],imageData=data,imageOriginalData='',imageCrop=None,imageOriginalWidth=0,imageOriginalHeight=0,imageRemoved=False)
   registry[name]=photo;r.pop('imageData',None);r.pop('imageOriginalData',None);prepared.append(r)
  seed['preparedResources']=prepared;seed['photoImages']=registry;seed['preparedImageUpgrades']={};seed['resources']=[];seed['examples']=[];seed['config']['storageNamespace']=key;seed['memberSchoolPolicy']={k:members[k] for k in ['fullMembers','aliases','sourceUrl','verifiedOn']};seed['memberSchoolPolicy']['selectionRule']='One published entry per primary member school in each AI-collection category. A school may appear in more than one category. AI Research: peer-reviewed journal articles published from 2021 onward; MDPI journals excluded.'
  seed['preparedAt']=catalog.get('exportedAt') or seed.get('preparedAt')
  encoded=json.dumps(seed,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
  updated=text[:match.start(1)]+encoded+text[match.end(1):]
  updated,n=re.subn(r"const KEY = '[^']+';",f"const KEY = '{key}';",updated,count=1);assert n==1
  updates.append((file,updated))
 # The default rebuild keeps the Pages entry point byte-identical to the full hub.
 # Derive it from the validated full-hub result, never from a stale index copy.
 if args.html is None:
  full_hub=HERE/'20261101Planning-Knowledge-Hub-Updated.html'
  full_result=next(updated for file,updated in updates if file==full_hub)
  updates.append((HERE/'index.html',full_result))
 # Validate every target before writing any HTML file.
 for file,updated in updates:file.write_text(updated,encoding='utf-8')
 counts={label:sum(domain in r.get('domains',[]) for r in rows) for label,domain in [('Teaching','Education'),('Research','Research'),('Applications','Practice')]}
 print(json.dumps({'updated':[str(f) for f,_ in updates],'resources':len(rows),'categories':counts,'note':'Rebuilt files start a fresh local browser workspace. Older browser workspaces remain separate; export them before switching files.'},indent=2))

if __name__=='__main__':main()
