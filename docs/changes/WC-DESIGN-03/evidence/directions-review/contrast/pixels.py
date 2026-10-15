from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
import io,json,math

def image(data):return Image.open(io.BytesIO(data)).convert('RGB')
def lum(c):
 a=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in c];return sum(a[i]*[.2126,.7152,.0722][i] for i in range(3))
def contrast(a,b):
 x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':900})
 for file,width,sel in [('04-home.html',1440,'.media-note'),('08-home.html',390,'h1'),('02-menu.html',390,'.breadcrumbs')]:
  page.set_viewport_size({'width':width,'height':900});page.goto('http://127.0.0.1:8875/'+file);page.evaluate('document.fonts.ready')
  info=page.locator(sel).evaluate('(el)=>({rect:el.getBoundingClientRect().toJSON(),color:getComputedStyle(el).color})');r=info['rect']
  box=(max(0,math.floor(r['left'])),max(0,math.floor(r['top'])),min(width,math.ceil(r['right'])),math.ceil(r['bottom']))
  snaps={}
  for c in ['transparent','black','white']:
   page.locator(sel).evaluate('(el,c)=>el.style.webkitTextFillColor=c',c)
   snaps[c]=image(page.screenshot(full_page=True)).crop(box)
  vals=[];fg=[int(x.strip()) for x in info['color'].split('(')[1].split(')')[0].split(',')[:3]]
  for x in range(snaps['white'].width):
   for y in range(snaps['white'].height):
    a=snaps['black'].getpixel((x,y));z=snaps['white'].getpixel((x,y));bg=snaps['transparent'].getpixel((x,y))
    if min(z[i]-a[i] for i in range(3))>150:vals.append((contrast(fg,bg),bg))
  print(json.dumps({'file':file,'width':width,'selector':sel,'fg':fg,'min_ratio':min(v[0] for v in vals) if vals else None,'samples':len(vals),'worst':min(vals) if vals else None,'rect':r}))
 b.close()
