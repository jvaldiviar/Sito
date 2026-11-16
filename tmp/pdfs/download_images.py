from bs4 import BeautifulSoup
from pathlib import Path
from urllib.request import urlretrieve
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess

root=Path('tmp/pdfs/images'); root.mkdir(parents=True,exist_ok=True)
urls=[]
for name in ['Flashbattery4.html','Flashbattery5.html']:
    s=BeautifulSoup(Path(name).read_text(),'html.parser')
    urls.extend(i['src'] for i in s.select('img[src]') if i['src'])
urls=list(dict.fromkeys(urls))
def fetch(pair):
    n,u=pair; p=root/f'{n:02}.png'
    if not p.exists(): subprocess.run(['curl','-f','-sS','-L','-A','Mozilla/5.0','-o',str(p),u],check=True)
    return u,str(p)
with ThreadPoolExecutor(max_workers=6) as pool:
    result=dict(pool.map(fetch,enumerate(urls)))
Path('tmp/pdfs/images.json').write_text(json.dumps(result))
print('Downloaded',len(result),'images')
