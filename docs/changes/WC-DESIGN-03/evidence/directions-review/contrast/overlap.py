from playwright.sync_api import sync_playwright
import json
JS='''()=>{const imgs=[...document.images].filter(i=>i.offsetWidth&&i.offsetHeight);let rs=[];for(let el of document.querySelectorAll('body *')){if(el.closest('svg,script,style'))continue;const s=getComputedStyle(el);if(!el.getClientRects().length||s.visibility==='hidden')continue;for(let t of el.childNodes){if(t.nodeType!==3||!t.textContent.trim())continue;let range=new Range();range.selectNode(t);for(let r of range.getClientRects()){let overlaps=imgs.filter(i=>{let x=i.getBoundingClientRect();return r.left<x.right&&r.right>x.left&&r.top<x.bottom&&r.bottom>x.top});if(overlaps.length)rs.push({tag:el.tagName,cls:el.className,text:t.textContent.slice(0,40),imgs:overlaps.map(i=>i.className||i.src.split('/').pop()),bg:s.backgroundColor});}}}return rs;}'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page()
 for width in [390,1440]:
  page.set_viewport_size({'width':width,'height':900})
  for i in range(1,11):
   for kind in ['home','menu']:
    f=f'{i:02}-{kind}.html';page.goto('http://127.0.0.1:8875/'+f);page.evaluate('document.fonts.ready');rows=page.evaluate(JS)
    if rows:print(f,width,json.dumps(rows,ensure_ascii=False))
 b.close()
