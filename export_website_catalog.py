#!/usr/bin/env python3
"""Export the ACSP workbook's Website Import sheet without third-party packages.

Usage: python export_website_catalog.py ACSP-Resource-Collection.xlsx --output-dir exports
The enhanced JSON and CSV target the companion HTML. The legacy JSON targets the
20261022 prototype and imports as drafts. Save/recalculate the workbook in Excel
after edits so formula cells contain up-to-date cached values.

Keep the bundled photos/ and figures/ directories and Image-Manifest.json beside
the workbook when exporting. JPEGs referenced by imageFile are embedded in the
enhanced JSON for offline portability.
The CSV retains 31 text/metadata columns without inline image payloads.
"""
import argparse
import base64
import csv
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, urlunsplit, unquote

HEADERS = ['id','title','url','institution','department','contributor','sourceTeam','date','description','shortDescription','domains','fields','topics','collectionIds','ownerGroupId','resourceType','method','keywords','audience','license','accessNotes','sourceStatus','imageFile','imageAlt','imageCredit','imageLicense','imageSource','verifiedOn','sourceEvidence','verificationNotes','isExample']
ARRAY_FIELDS = {'domains','fields','topics','collectionIds','keywords'}
LEGACY_FIELDS = ['id','title','description','url','domains','fields','topics','collectionIds','ownerGroupId','resourceType','method','keywords','institution','contributor','date','geography','license','audience','isExample']
TYPES = {'Course / Syllabus','Teaching Material','Publication','Research Project','Dataset','Code / Notebook','Tool','Workflow','Use Case','Policy / Guidance','Report','Event / Recording','Other'}
FIELDS = {'planning','policy','geography','design','environment','health','computing','interdisciplinary'}
LIMITS = {'id':100,'title':160,'url':1500,'institution':180,'department':350,'contributor':120,'sourceTeam':1200,'date':60,'description':3500,'shortDescription':900,'ownerGroupId':100,'resourceType':60,'method':120,'audience':180,'license':700,'accessNotes':1000,'sourceStatus':250,'imageFile':40,'imageAlt':500,'imageCredit':500,'imageLicense':300,'imageSource':1500,'verifiedOn':30,'sourceEvidence':12000,'verificationNotes':4000}
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
PHOTO_FILE = re.compile(r'photos/(teaching|research|applications)-[0-9]{2}\.jpg\Z')
FIGURE_FILE = re.compile(r'figures/research-[0-9]{2}\.jpg\Z')
CATEGORY_COVERS = {'teaching.svg','research.svg','applications.svg'}
MAX_PHOTO_BYTES = 80_000

def read_sheet(path, sheet_name='Website Import'):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheet = next((s for s in workbook.findall('s:sheets/s:sheet',NS) if s.attrib['name']==sheet_name),None)
        if sheet is None:
            raise ValueError(f'Missing worksheet: {sheet_name}')
        target=rels[sheet.attrib['{'+NS['r']+'}id']]
        sheet_path=target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl')/target)
        root=ET.fromstring(z.read(sheet_path))
        rows=[]
        for row in root.findall('s:sheetData/s:row',NS):
            values={}
            for cell in row.findall('s:c',NS):
                ref=cell.attrib['r']; letters=re.match('[A-Z]+',ref).group(); index=0
                for char in letters: index=index*26+ord(char)-64
                typ=cell.attrib.get('t'); value=cell.find('s:v',NS); formula=cell.find('s:f',NS)
                if typ=='inlineStr':
                    inline=cell.find('s:is',NS); text=''.join(inline.itertext()) if inline is not None else ''
                elif value is not None:
                    text=value.text or ''
                    if typ=='s': text=shared[int(text)]
                    elif typ=='b': text='true' if text=='1' else 'false'
                    elif typ=='e': raise ValueError(f'Excel error {text} in {sheet_name}!{ref}')
                else:
                    # Exporters commonly represent a calculated empty text value
                    # as t="str" without a <v> element (for example imageAlt).
                    if formula is not None and typ!='str':
                        raise ValueError(f'{sheet_name}!{ref} has no cached formula value. Open, recalculate and save the workbook in Excel, then export again.')
                    text=''
                values[index-1]=text
            rows.append(values)
        if not rows: raise ValueError('Website Import is empty.')
        header=[str(rows[0].get(i,'')).strip() for i in range(max(rows[0])+1)]
        if header!=HEADERS:
            raise ValueError('Website Import row 1 must contain the documented 31 machine headers, in order.')
        records=[{h:str(row.get(i,'')).strip() for i,h in enumerate(header)} for row in rows[1:] if any(str(v).strip() for v in row.values())]
        properties=workbook.find('s:workbookPr',NS)
        epoch=dt.date(1904,1,1) if properties is not None and properties.attrib.get('date1904') in ('1','true') else dt.date(1899,12,30)
        for record in records:
            value=record.get('verifiedOn','')
            if re.fullmatch(r'\d+(?:\.0+)?',value):
                record['verifiedOn']=(epoch+dt.timedelta(days=int(float(value)))).isoformat()
        return records

def http_url(value):
    parts=urlsplit(value)
    if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:
        raise ValueError('Use an http(s) source URL without embedded credentials.')
    return urlunsplit((parts.scheme,parts.netloc.lower(),parts.path,parts.query,'' )).rstrip('/')

def normalize(raw):
    rec={k:str(raw.get(k,'')).strip() for k in HEADERS if k not in ARRAY_FIELDS and k!='isExample'}
    for key in ARRAY_FIELDS:
        value=raw.get(key,[])
        if not isinstance(value,list): value=str(value).split(';')
        rec[key]=list(dict.fromkeys(str(x).strip() for x in value if str(x).strip()))
        if len(rec[key])>30 or any(len(v)>140 for v in rec[key]): raise ValueError(f'{key} must be a short list of text values.')
    value=raw.get('isExample',False)
    if value is True or str(value).lower() in ('true','1','yes'): rec['isExample']=True
    elif value is False or str(value).lower() in ('false','0','no',''): rec['isExample']=False
    else: raise ValueError('isExample must be true or false.')
    for key,maximum in LIMITS.items():
        if len(rec.get(key,''))>maximum: raise ValueError(f'{key} exceeds {maximum} characters.')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,99}',rec['id']): raise ValueError('Invalid stable resource ID.')
    for key in ('title','url','description','institution','resourceType','ownerGroupId'):
        if not rec[key]: raise ValueError(f'{key} is required.')
    count=len(rec['description'].split())
    if not 20<=count<=150: raise ValueError(f'description must contain 20–150 words (currently {count}).')
    http_url(rec['url'])
    if not rec['domains'] or set(rec['domains'])-{'Education','Research','Practice'}: raise ValueError('Unknown domain.')
    if not rec['fields'] or set(rec['fields'])-FIELDS: raise ValueError('Unknown field ID.')
    if set(rec['topics'])-{f'track-{i}' for i in range(1,13)}: raise ValueError('Unknown topic ID.')
    if set(rec['collectionIds'])-{'ai-in-planning','community-and-housing','environment-and-climate','planning-education'}: raise ValueError('Unknown collection ID.')
    if rec['ownerGroupId'] not in {'group-ai','group-housing','group-climate','group-education'}: raise ValueError('Unknown steward group.')
    if rec['resourceType'] not in TYPES: raise ValueError('Unknown resource type.')
    if rec['imageFile'] and rec['imageFile'] not in CATEGORY_COVERS and not PHOTO_FILE.fullmatch(rec['imageFile']) and not FIGURE_FILE.fullmatch(rec['imageFile']):
        raise ValueError('imageFile must name a bundled category cover, photos/<category>-NN.jpg, or figures/research-NN.jpg; other paths are not accepted.')
    if rec['verifiedOn']:
        try: dt.date.fromisoformat(rec['verifiedOn'])
        except ValueError as exc: raise ValueError('verifiedOn must be YYYY-MM-DD.') from exc
    return rec

def jpeg_dimensions(raw):
    """Read bounded JPEG frame dimensions without third-party imaging packages."""
    if not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):
        raise ValueError('Photo asset is not a complete JPEG file.')
    position=2
    frames={0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
    while position+3<len(raw):
        if raw[position]!=0xFF:
            raise ValueError('Invalid JPEG marker sequence.')
        while position<len(raw) and raw[position]==0xFF:
            position+=1
        if position>=len(raw): break
        marker=raw[position]; position+=1
        if marker in (0xD8,0x01) or 0xD0<=marker<=0xD7:
            continue
        if marker in (0xD9,0xDA): break
        if position+2>len(raw): break
        length=int.from_bytes(raw[position:position+2],'big')
        if length<2 or position+length>len(raw):
            raise ValueError('Invalid JPEG segment length.')
        if marker in frames:
            if length<8: raise ValueError('Invalid JPEG frame.')
            height=int.from_bytes(raw[position+3:position+5],'big')
            width=int.from_bytes(raw[position+5:position+7],'big')
            if width<1 or height<1: raise ValueError('Invalid JPEG dimensions.')
            return width,height
        position+=length
    raise ValueError('Photo asset has no valid JPEG frame.')

def image_contexts(asset_dirs):
    """Read attribution context from the packaged image manifest when present."""
    result={}
    for root in dict.fromkeys(Path(p).resolve() for p in asset_dirs):
        for path in (root/'Image-Manifest.json',root/'figures'/'manifest.json'):
            if not path.is_file(): continue
            data=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data,list):
                raise ValueError(f'Image manifest must contain an array: {path.name}.')
            for entry in data:
                if not isinstance(entry,dict): raise ValueError('Image manifest entries must be objects.')
                name=entry.get('imageFile') or entry.get('file','')
                if not PHOTO_FILE.fullmatch(name) and not FIGURE_FILE.fullmatch(name):
                    raise ValueError('Image manifest contains an unsupported image path.')
                context=entry.get('imageContext') or entry.get('imageRole','')
                if not isinstance(context,str) or not context.strip() or len(context)>250:
                    raise ValueError(f'Image manifest needs a short imageContext or imageRole for {name}.')
                # Older figure manifests express figure number separately.
                number=entry.get('figureNumber','')
                if number and not entry.get('imageContext'):
                    context=f'{context} · {number}'
                result[name]=context.strip()
    return result

def attach_photo(rec, asset_dirs, contexts=None):
    """Embed a named, verified-size local photo; never resolve arbitrary paths."""
    match=PHOTO_FILE.fullmatch(rec.get('imageFile',''))
    figure=FIGURE_FILE.fullmatch(rec.get('imageFile',''))
    if not match and not figure: return
    relative=PurePosixPath(rec['imageFile'])
    roots=list(dict.fromkeys(Path(p).resolve() for p in asset_dirs))
    asset=None
    for root in roots:
        candidate=(root/relative).resolve()
        try: candidate.relative_to(root)
        except ValueError: continue
        if candidate.is_file():
            asset=candidate; break
    if asset is None:
        raise ValueError(f"Missing photo asset: {rec['imageFile']}. Keep photos/ beside the workbook or output directory.")
    if asset.stat().st_size>MAX_PHOTO_BYTES:
        raise ValueError(f"Photo asset exceeds {MAX_PHOTO_BYTES:,} bytes: {rec['imageFile']}.")
    raw=asset.read_bytes()
    if jpeg_dimensions(raw)!=(800,450):
        raise ValueError(f"Bundled photo must be 800 × 450 pixels: {rec['imageFile']}.")
    for key in ('imageAlt','imageCredit','imageLicense','imageSource'):
        if not rec.get(key): raise ValueError(f"{key} is required for photo asset {rec['imageFile']}.")
    http_url(rec['imageSource'])
    rec['imageData']='data:image/jpeg;base64,'+base64.b64encode(raw).decode('ascii')
    context=(contexts or {}).get(rec['imageFile'])
    if figure and not context:
        raise ValueError(f"Figure context is missing for {rec['imageFile']}. Keep Image-Manifest.json beside the workbook.")
    rec['imageContext']=context or ('Institutional context photo' if match.group(1)=='teaching' else 'Planning context photo')

def verify_member_schools(records, asset_dirs):
    """One represented ACSP Full Member university per AI category."""
    ai=[r for r in records if 'ai-in-planning' in r.get('collectionIds',[])]
    if not ai: return
    path=next((Path(root)/'ACSP-Member-School-Reference.json' for root in asset_dirs if (Path(root)/'ACSP-Member-School-Reference.json').is_file()),None)
    if path is None:
        raise ValueError('Keep ACSP-Member-School-Reference.json beside the workbook to validate AI-collection schools.')
    members=json.loads(path.read_text(encoding='utf-8'))
    names={name.casefold():name for name in members['fullMembers']}
    for alias,canonical in members.get('aliases',{}).items():
        if canonical in members['fullMembers']:names[alias.casefold()]=canonical
    seen={}
    labels={'Education':'Teaching','Research':'Research','Practice':'Applications'}
    for r in ai:
        school=names.get(r['institution'].strip().casefold())
        if not school:
            raise ValueError(f"{r['id']}: choose one primary university from the ACSP Full Member reference.")
        r['institution']=school
        for domain in r['domains']:
            key=(domain,school)
            if key in seen:
                raise ValueError(f"{labels[domain]} already contains {school} ({seen[key]}). Keep one entry per school in each category; edit that entry or choose another school ({r['id']}).")
            seen[key]=r['id']

def verify_research_journals(records):
    """Validate the deterministic AI Research publication policy, not journal rankings."""
    for record in records:
        if 'ai-in-planning' not in record.get('collectionIds',[]) or 'Research' not in record.get('domains',[]): continue
        label=record['id']
        if record.get('resourceType')!='Publication':
            raise ValueError(f'{label}: AI Research entries must be published journal papers.')
        if not re.fullmatch(r'Peer-reviewed journal article · .+',record.get('sourceStatus',''),re.I):
            raise ValueError(f'{label}: record the peer-reviewed journal name in Source Status as "Peer-reviewed journal article · Journal name".')
        years=[int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b',record.get('date',''))]
        if not years or min(years)<2021:
            raise ValueError(f'{label}: AI Research journal papers must be published from 2021 onward.')
        url=record['url'];parts=urlsplit(url);host=(parts.hostname or '').lower()
        if host=='arxiv.org' or host.endswith('.arxiv.org'):
            raise ValueError(f'{label}: link to the published journal article, not an arXiv-only record.')
        if host=='mdpi.com' or host.endswith('.mdpi.com') or re.search(r'10\.3390(?:/|$|[?#])',unquote(url).lower()) or 'mdpi' in record.get('sourceStatus','').lower():
            raise ValueError(f'{label}: MDPI journals are excluded from this AI Research collection.')

def export(rows, output_dir, asset_dirs=None):
    records=[]; ids=set(); urls=set()
    asset_dirs=asset_dirs or [output_dir]
    contexts=image_contexts(asset_dirs)
    for index,row in enumerate(rows,2):
        try:
            rec=normalize(row); canonical=http_url(rec['url'])
            attach_photo(rec,asset_dirs,contexts)
            if rec['id'] in ids: raise ValueError('Duplicate resource ID.')
            if canonical in urls: raise ValueError('Duplicate source URL.')
            ids.add(rec['id']); urls.add(canonical); records.append(rec)
        except ValueError as exc: raise ValueError(f'Website Import row {index}: {exc}') from exc
    if not records: raise ValueError('No resource rows were found.')
    verify_member_schools(records,asset_dirs)
    verify_research_journals(records)
    if len(records)>500: raise ValueError('The prototype supports at most 500 resources.')
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    common={'schemaVersion':3,'kind':'catalog','exportedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'notice':'Prepared resource collection. Import as drafts for review, or use the companion HTML Publisher action to import a reviewed snapshot. This file does not assert official ACSP editorial approval.'}
    enhanced={**common,'resources':records}
    legacy={**common,'resources':[{key:rec.get(key,'' if key not in ARRAY_FIELDS else []) for key in LEGACY_FIELDS} for rec in records]}
    outputs=[]
    for name,data in [('ACSP-Website-Catalog.json',enhanced),('ACSP-Original-Prototype-Catalog.json',legacy)]:
        path=output_dir/name; path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); outputs.append(path)
    csv_path=output_dir/'ACSP-Website-Import.csv'
    with csv_path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=HEADERS); writer.writeheader()
        for rec in records:
            writer.writerow({h:'; '.join(rec[h]) if h in ARRAY_FIELDS else str(rec[h]).lower() if h=='isExample' else rec[h] for h in HEADERS})
    outputs.append(csv_path)
    return records,outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('workbook',type=Path)
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    try:
        output_dir=args.output_dir or args.workbook.parent
        records,paths=export(read_sheet(args.workbook),output_dir,[args.workbook.parent,output_dir])
    except (ValueError,KeyError,zipfile.BadZipFile,ET.ParseError,OSError) as exc:
        print(f'Export failed: {exc}',file=sys.stderr); return 1
    counts={name:sum(domain in r['domains'] for r in records) for name,domain in [('Teaching','Education'),('Research','Research'),('Applications','Practice')]}
    print(json.dumps({'records':len(records),'categories':counts,'files':[str(p.resolve()) for p in paths]},indent=2)); return 0

if __name__=='__main__':
    raise SystemExit(main())
