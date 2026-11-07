"""Download public map context once; notebooks use cached sources offline."""
from pathlib import Path
import requests,json,hashlib,datetime,io,zipfile
BASE=Path(__file__).resolve().parent
OUT=BASE/'reference_data'; OUT.mkdir(exist_ok=True)
records=[]
def fetch(name,url,query=None):
    p=OUT/name
    if not p.exists():
        print('Downloading',name,flush=True)
        r=requests.post(url,data={'data':query},timeout=180) if query else requests.get(url,timeout=180)
        r.raise_for_status()
        if name.endswith('.json') or name.endswith('.geojson'):
            payload=r.json()
            if 'remark' in payload: raise RuntimeError(payload['remark'])
        if name.endswith('.xlsx') and not r.content.startswith(b'PK'): raise ValueError('Not an Excel response')
        p.write_bytes(r.content)
    records.append(dict(file=name,url=url,query=query,downloaded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (OUT/'sources.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('Saved',name,p.stat().st_size,flush=True)
fetch('belgium_2024.geojson','https://gisco-services.ec.europa.eu/distribution/v2/countries/distribution/BE-region-01m-4326-2024.geojson')
class RemoteZip(io.RawIOBase):
    def __init__(self,url):
        self.url=url; self.pos=0
        r=requests.get(url,headers={'Range':'bytes=-65536'},timeout=60); r.raise_for_status()
        if r.status_code!=206: raise RuntimeError('Server does not support selective ZIP download')
        self.size=int(r.headers['Content-Range'].split('/')[-1]); self.tail=r.content
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else (self.pos+offset if whence==1 else self.size+offset)
        return self.pos
    def read(self,n=-1):
        end=self.size if n<0 else min(self.size,self.pos+n)
        if self.pos>=self.size: return b''
        if self.pos>=self.size-len(self.tail): data=self.tail[self.pos-(self.size-len(self.tail)):end-(self.size-len(self.tail))]
        else:
            r=requests.get(self.url,headers={'Range':f'bytes={self.pos}-{end-1}'},timeout=180); r.raise_for_status()
            assert r.status_code==206; data=r.content
            assert len(data)==end-self.pos, (len(data),end-self.pos)
        self.pos=end; return data
url='https://download.geofabrik.de/europe/belgium-250101-free.shp.zip'
roads=OUT/'roads'; roads.mkdir(exist_ok=True)
if not (roads/'gis_osm_roads_free_1.shp').exists():
    with zipfile.ZipFile(RemoteZip(url)) as z:
        for item in z.infolist():
            if Path(item.filename).stem=='gis_osm_roads_free_1':
                print('Downloading roads layer',item.filename,item.compress_size,flush=True)
                (roads/Path(item.filename).name).write_bytes(z.read(item))
for p in roads.iterdir():
    records.append(dict(file=str(p.relative_to(OUT)),url=url,snapshot='2025-01-01',downloaded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),licence='OpenStreetMap contributors, ODbL 1.0; Geofabrik extract'))
(OUT/'sources.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
try: fetch('statbel_map_variables.xlsx','https://statbel.fgov.be/sites/default/files/files/opendata/Accident_XY/VAR_LIST_ACC_OPENDATA_MAP.xlsx')
except Exception as e: print('Metadata download unavailable:',str(e),flush=True)
