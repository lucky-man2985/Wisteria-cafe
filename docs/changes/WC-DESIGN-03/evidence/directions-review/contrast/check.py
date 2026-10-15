import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path('/workspace/scratch/wisteria-design-03/directions-review/contrast')
JS='''() => {
 const rgb = val => {const n=val.match(/[\\d.]+/g);return n ? [...n.slice(0,3).map(Number), n.length>3?Number(n[3]):1] : [0,0,0,0]};
 const over=(fg,bg) => {let a=fg[3]+bg[3]*(1-fg[3]);return [0,1,2].map(i=>(fg[i]*fg[3]+bg[i]*bg[3]*(1-fg[3]))/(a||1)).concat([a])};
 const lum=c=>{let x=c.map(v=>{v=v/255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*x[0]+.7152*x[1]+.0722*x[2]};
 const cr=(a,b)=>{let x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
 const selector=el=>{ if(el.id)return '#'+el.id;let s=el.tagName.toLowerCase()+[...el.classList].map(x=>'.'+x).join('');let p=el.parentElement;if(p && [...p.children].filter(x=>x.tagName===el.tagName).length>1)s+=':nth-of-type('+([...p.children].filter(x=>x.tagName===el.tagName).indexOf(el)+1)+')';return (p && p!==document.body? p.tagName.toLowerCase()+[...p.classList].map(x=>'.'+x).join('')+' > ':'')+s;};
 const visible=el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return !!el.getClientRects().length && r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden' && s.opacity!=='0'};
 const results=[];
 for(const el of document.querySelectorAll('body *')){
 if(!visible(el)||el.closest('svg,script,style'))continue;
 let text=[...el.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(' ').replace(/\\s+/g,' ').trim();
 if(!text && !el.matches('input[placeholder],select'))continue;
 let s=getComputedStyle(el);let placeholder=false;
 if(el.matches('input[placeholder]')&&!el.value){text=el.placeholder;s=getComputedStyle(el,'::placeholder');placeholder=true;}
 else if(el.matches('select'))text=el.options[el.selectedIndex]?.text||'';
 if(!text)continue;
 let chain=[],opacities=[];for(let p=el;p;p=p.parentElement){let ps=getComputedStyle(p);let color=rgb(ps.backgroundColor);if(color[3]>0)chain.push({selector:selector(p),color});if(Number(ps.opacity)<1)opacities.push({selector:selector(p),opacity:ps.opacity});}
 let bg=[255,255,255,1];for(let i=chain.length-1;i>=0;i--)bg=over(chain[i].color,bg);
 let fg=over(rgb(s.color),bg);let ratio=cr(fg,bg);let size=parseFloat(s.fontSize),weight=parseInt(s.fontWeight)||400;let large=size>=24||size>=18.6667&&weight>=700;
 results.push({selector:selector(el)+(placeholder?'::placeholder':''),text:text.slice(0,80),fg:s.color,bg:bg.slice(0,3).map(v=>+v.toFixed(2)),ratio:+ratio.toFixed(3),size,weight,large,fail:ratio<(large?3:4.5),chain,opacities});
 }
 return results;
}'''
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 results=[]
 for width in [390,1440]:
  page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
  for id in range(1,11):
   for kind in ['home','menu']:
    file=f'{id:02}-{kind}.html';page.goto('http://127.0.0.1:8875/'+file);page.evaluate('document.fonts.ready')
    rows=page.evaluate(JS)
    results.append({'file':file,'width':width,'rows':rows})
    failures=[r for r in rows if r['fail']]
    print(file,width,'rows',len(rows),'fail',len(failures))
    for r in failures:print(json.dumps(r,ensure_ascii=False))
  page.close()
 browser.close()
 (ROOT/'computed.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
