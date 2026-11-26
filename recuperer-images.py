"""Télécharge les médias publics du site client, sans dépendance externe. Python 3."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit, unquote
from html.parser import HTMLParser
import re, hashlib, json, shutil
ROOT=Path(__file__).resolve().parent; DEST=ROOT/'images'; DEST.mkdir(exist_ok=True)
BASE='https://www.daussy-couverture.fr'; PHOTO=BASE+'/lib/tiny_mce/source/491353515_122152187234561526_2715716231290627199_n.jpg'; LOGO=BASE+'/img/elementgraphique/element_graphique_3.webp'
PAGES={'accueil':'/','couverture':'/couverture-ardoises/c-3.html','zinguerie':'/zinguerie/c-21.html','bardage':'/bardage/c-22.html','album':'/album/couvertures-ardoises/a-2','galerie':'/album'}
def get(url):
 with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; SiteRedesign/1.0)'}),timeout=25) as r: return r.read(),r.headers.get('Content-Type','')
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if not v:continue
   if k in ('srcset','data-srcset'):
    self.urls.extend(x.strip().split()[0] for x in v.split(',') if x.strip())
   elif k in ('src','href','data-src','data-original','data-lazy','data-image','data-bg','data-background','data-full','data-large','data-zoom-image'):self.urls.append(v)
   elif k=='style':self.urls.extend(re.findall(r'url\([\'\"]?([^\)\'\"]+)',v))
def save(url,path):
 data,typ=get(url)
 if not typ.startswith('image/'):raise ValueError('Réponse non image : '+typ)
 path.write_bytes(data);return len(data)
manifest={}
for url,name in [(PHOTO,'chantier.jpg'),(LOGO,'logo.webp')]:
 try:save(url,DEST/name);print('OK',name)
 except Exception as e:print('ÉCHEC',name,e)
for role,route in PAGES.items():
 url=BASE+route
 try:
  data,_=get(url);html=data.decode('utf-8','replace');parser=Parser();parser.feed(html); urls=parser.urls+re.findall(r'url\([\'\"]?([^\)\'\"]+)',html)+re.findall(r'[\'\"]([^\'\"<>\s]+\.(?:jpg|jpeg|png|webp))(?:\?[^\'\"<>\s]*)?[\'\"]',html,re.I)
  seen=set(); found=[]
  for ref in urls:
   full=urljoin(url,ref); parts=urlsplit(full)
   if parts.hostname not in ('www.daussy-couverture.fr','daussy-couverture.fr') or not re.search(r'\.(jpg|jpeg|png|webp)$',parts.path,re.I) or full in seen:continue
   seen.add(full); ext=Path(parts.path).suffix.lower(); filename=hashlib.sha256(full.encode()).hexdigest()[:12]+ext
   try:
    target=DEST/filename
    if not target.exists():save(full,target)
    found.append({'url':full,'fichier':filename,'octets':target.stat().st_size})
   except Exception as e:print('ÉCHEC',full,e)
  manifest[role]=found;print(role,':',len(found),'images')
 except Exception as e:print('ÉCHEC page',url,e)
(ROOT/'inventaire-images.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# Only known authentic photo is applied automatically. Assign further files after visual inspection.
if (DEST/'chantier.jpg').exists():
 for role in ('couverture','zinguerie','bardage','approche','zone'):
  path=DEST/(role+'.jpg')
  if not path.exists():shutil.copyfile(DEST/'chantier.jpg',path)
print('Terminé. Inventaire : inventaire-images.json. Vérifiez visuellement les photos avant de les affecter aux différentes rubriques.')
