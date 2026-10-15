import json,runpy
from pathlib import Path
from playwright.sync_api import sync_playwright
source=Path('/workspace/scratch/wisteria-design-03/directions-review/contrast/check.py').read_text()
JS=source.split("JS='''",1)[1].split("'''",1)[0]
# Restore Python's JavaScript-string backslash escapes exactly as the source module did.
JS=JS.replace('\\\\','\\')
tasks=[('01-menu.html',1440,'.category-sidebar a.active small'),('06-menu.html',1440,'.category-sidebar a.active small'),('03-menu.html',390,'input::placeholder'),('03-menu.html',1440,'input::placeholder')]
for n in ['07','09']:
 for k in ['home','menu']:
  for w in [390,1440]:tasks.append((f'{n}-{k}.html',w,'.footer-inner p'))
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page()
 for file,width,selector in tasks:
  page.set_viewport_size({'width':width,'height':900});page.goto('http://127.0.0.1:8875/'+file);page.evaluate('document.fonts.ready')
  rows=page.evaluate(JS)
  if selector=='.category-sidebar a.active small':matches=[r for r in rows if r['selector']=='a.active > small']
  elif selector=='input::placeholder':matches=[r for r in rows if r['selector'].endswith('input::placeholder')]
  else:matches=[r for r in rows if r['text']=='Кофе • еда • десерты · Севастополь']
  assert len(matches)==1,(file,width,selector,matches)
  result={'file':file,'width':width,'target':selector,**matches[0]};results.append(result)
  print(json.dumps({k:result[k] for k in ['file','width','target','fg','bg','ratio','size','fail']},ensure_ascii=False))
 browser.close()
Path('/workspace/scratch/wisteria-design-03/directions-review/contrast/recheck.json').write_text(json.dumps({'pass':all(not x['fail'] for x in results),'checks':results},ensure_ascii=False,indent=2))
