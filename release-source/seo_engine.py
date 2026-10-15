"""Portable HTML SEO build; preferred legacy URLs stay on wisteriacafe.ru."""
import html,json,re,pathlib,collections,urllib.parse,math
E=html.escape
PRODUCTION_ORIGIN='https://wisteriacafe.ru'
PREVIEW_ORIGIN='https://wisteria-cafe-new.lackyman2985.chatgpt.site'
PREFERRED={
 '/menu/':'/edasevastopol','/menu/breakfast/':'/zakazatzavtraksevastopol',
 '/menu/salads/':'/salatysevastopol','/menu/bowls/':'/boulysevastopol',
 '/menu/soups/':'/supsevastopol','/menu/hot/':'/goryacheesevastopol',
 '/menu/lunch/':'/kompleksnye-obedy','/menu/plant/':'/veganskieproduktysevastopol',
 '/menu/tortillas/':'/tortilisevastopol','/menu/sandwiches/':'/sendvichi',
 '/menu/spring-rolls/':'/rollysevastopol','/menu/oat-pancakes/':'/ovsyanobliny',
 '/menu/bakery/':'/vypechkasevastopol','/menu/desserts/':'/desertysevastopol',
 '/menu/pp-desserts/':'/kupitdesertysevastopol','/menu/drinks/':'/kofesevastopol',
 '/menu/cakes/':'/dostavka-tortov','/menu/extras/':'/dopolnitelnokzakazu',
 '/delivery/':'/dostavkasevastopol','/contacts/':'/kontakty','/about/':'/onas',
 '/privacy/':'/politikakonfidentsialnosti','/blog/':'/blog_o_ede','/site-map/':'/karta_sayta',
}
def preferred(path):return PREFERRED.get(path,path)
def plain(s):return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',str(s))).strip()
def amount(n):return f'{float(n):g}'+' ₽'
def asset_url(origin,path):return origin+path if path.startswith('/') else path
def file_for(root,path):
 if path=='/':return root/'index.html'
 if path.endswith('.html'):return root/path.lstrip('/')
 return root/path.strip('/')/'index.html'

EDITORIAL_NAMES={
 'boulysevastopol-1614885300332':'Боул с индейкой',
 'boulysevastopol-1614193782154':'Боул с креветкой и кальмаром',
 'syrnikiizapekanki-1614193862630':'Классические запечённые сырники',
 'syrnikiizapekanki-1614193782154':'Запечённые сырники с изюмом',
 'kupitdesertysevastopol-1620761100128':'Шоколад и вишня',
 'kupitdesertysevastopol-1647884065754':'Манго и маракуйя',
 'salatysevastopol-1615226157829':'Салат с авокадо и бэби моцареллой',
 'salatysevastopol-1615226216766':'Салат со свёклой и сыром фета',
 'supsevastopol-1615225429309':'Сырный сливочный крем-суп',
 'supsevastopol-1620322951888':'Грибной сливочный крем-суп'
}
def display_name(p):
 if p['id'] in EDITORIAL_NAMES:return EDITORIAL_NAMES[p['id']]
 name=re.sub(r'\s*\*?ВРЕМЕННО НЕДОСТУПЕН\*?','',p['name'],flags=re.I).strip()
 return re.sub(r'\s+[си] гарниром на выбор\.?$','',name,flags=re.I)

def static_card(p):
 name=display_name(p)
 comp=plain(p.get('composition',''));comp=comp[:117].rsplit(' ',1)[0]+'…' if len(comp)>120 else comp
 price=p.get('priceFrom',p['price']);variable=bool(p.get('optionPrices'))
 image=f'<img src="{E(p["image"])}" alt="{E(name)}" loading="lazy" width="900" height="600">' if p['image'] else '<span>Фото уточняется</span>'
 control=f'<button class="card-add" data-add="{E(p["id"])}">'+('Выбрать' if p['options'] else 'Добавить')+' <span aria-hidden="true">+</span></button>' if p.get('available',True) else '<button class="card-add" disabled>Недоступно</button>'
 issues=f'<div class="card-options-note"><a href="/dish/{p["id"]}/">Данные требуют уточнения</a></div>' if p.get('sourceIssues') else ''
 meta=f'<span class="card-category">{E(p["category"])}</span>'+(f'<span class="card-weight">{E(p["weight"])}</span>' if p.get('weight') else '')
 return f'<article class="card"><button class="favorite" data-favorite="{E(p["id"])}" aria-pressed="false" aria-label="В избранное: {E(name)}">♡</button><a class="card-image" href="/dish/{p["id"]}/">{image}<span class="quick-cue">Подробнее</span></a><div class="card-body"><div class="meta">{meta}</div><h3><a href="/dish/{p["id"]}/">{E(name)}</a></h3><p class="card-teaser">{E(comp) if comp else "Состав и детали уточните у кафе."}</p><div class="allergen-summary">{E("По составу: "+", ".join(p["allergens"])) if comp and p["allergens"] else "Полный состав и аллергены уточняются"}</div>{issues}<div class="card-actions"><span class="price">{"от " if variable else ""}{amount(price)}</span><div class="card-control" data-card-control="{E(p["id"])}">{control}</div></div></div></article>'

def copy_block(row,links=None):
 paragraphs=row.get('paragraphs',[])
 if isinstance(paragraphs,str):paragraphs=[paragraphs]
 sections=''.join('<h3>'+E(v['heading'])+'</h3><p>'+E(v['text'])+'</p>' for v in row.get('sections',[]))
 related=links or []
 links_html='<div class="order-actions">'+''.join('<a class="btn light" href="'+E(p)+'">'+E(label)+'</a>' for p,label in related)+'</div>' if related else ''
 questions=[(v.get('question',''),v.get('answer','')) if isinstance(v,dict) else v for v in row.get('faq',[])]
 faq=''.join('<details><summary>'+E(q)+'</summary><p>'+E(a)+'</p></details>' for q,a in questions)
 return '<section class="container content"><h2>'+E(row.get('sectionTitle','Меню и заказ в Wisteria'))+'</h2>'+''.join('<p>'+E(v)+'</p>' for v in paragraphs)+sections+links_html+('<div class="faq">'+faq+'</div>' if faq else '')+'</section>'

class SEOBuilder:
 def __init__(self,root,output,products,origin,production,categories):
  self.root=root;self.output=output;self.products=products;self.origin=origin;self.production=production;self.categories=categories;self.pages={};self.redirects={};self.source_inventory={};self.product_titles={};self.verify={}
  f=root/'seo-source-inventory.json'
  if f.exists():
   self.source_inventory=json.loads(f.read_text())
   for p in self.source_inventory.get('pages',[]):
    if p.get('sourcePath')=='/':
     self.verify={t['name']:t['content'] for t in p.get('metaTags',[]) if t.get('name') in ['yandex-verification','google-site-verification'] and t.get('content')}
  names=collections.Counter(p['name']for p in products);used=set()
  for p in products:
   title=display_name(p)
   if names[p['name']]>1:title+=' — '+(p.get('weight') or amount(p.get('priceFrom',p['price'])))
   if title in used:title+=' · '+plain(p['description']).split('\n')[0][:45]
   if title in used:title+=' · вариант '+str(sum(x.startswith(title)for x in used)+1)
   self.product_titles[p['id']]=title;used.add(title)
 def body_links(self,body):
  return re.sub(r'(href=")([^"#?]+)(")',lambda m:m[1]+preferred(m[2])+m[3],body)
 def category_path(self,cat):return preferred('/menu/'+(self.categories[cat]+'/' if self.categories[cat] else ''))
 def graph(self,path,title,kind,provided,rows,social_image=None):
  url=self.origin+path;brand=self.origin+'/#brand';website=self.origin+'/#website'
  entities=[{'@type':'Organization','@id':brand,'name':'Wisteria cafe','alternateName':'Вистерия кафе','url':self.origin+'/','logo':self.origin+'/assets/wisteria-logo.svg','telephone':'+79780711812','email':'wisteriacafe@mail.ru'},
  {'@type':'WebSite','@id':website,'name':'Wisteria cafe','url':self.origin+'/','inLanguage':'ru-RU','publisher':{'@id':brand}}]
  if path in ['/','/kontakty','/onas']:
   for slug,address in [('petrova','Генерала Петрова, 4'),('karantinnaya','Карантинная, 23')]:
    entities.append({'@type':'CafeOrCoffeeShop','@id':self.origin+'/#cafe-'+slug,'name':'Wisteria cafe','url':self.origin+'/kontakty','telephone':'+79780711812','parentOrganization':{'@id':brand},'address':{'@type':'PostalAddress','streetAddress':address,'addressLocality':'Севастополь','addressCountry':'RU'},'hasMenu':self.origin+'/edasevastopol','servesCuisine':['Кафе','Завтраки','Вегетарианские блюда']})
  web={'@type':'CollectionPage' if kind=='menu' else 'WebPage','@id':url+'#webpage','url':url,'name':title,'inLanguage':'ru-RU','isPartOf':{'@id':website}}
  entities.append(web)
  primary_image=None
  if social_image:
   primary_image={'@type':'ImageObject','@id':url+'#primary-image','contentUrl':asset_url(self.origin,social_image['src']),'url':asset_url(self.origin,social_image['src']),'width':int(social_image['width']),'height':int(social_image['height']),'caption':social_image['alt']}
   entities.append(primary_image);web['primaryImageOfPage']={'@id':primary_image['@id']}
  if kind=='article':
   article={'@type':'Article','@id':url+'#article','headline':title,'mainEntityOfPage':{'@id':url+'#webpage'},'author':{'@id':brand},'publisher':{'@id':brand},'inLanguage':'ru-RU'}
   if primary_image:article['image']={'@id':primary_image['@id']}
   entities.append(article);web['mainEntity']={'@id':article['@id']}
  if provided and provided.get('@type')=='MenuItem':
   p=next(p for p in self.products if '/dish/'+p['id']+'/'==path)
   item={k:v for k,v in provided.items()if k!='@context'};item['@id']=url+'#menu-item';item['offers']['url']=url
   if p.get('available',True):item['offers'].pop('availability',None)
   item['image']=asset_url(self.origin,p['image']) if p['image'] else None
   item={k:v for k,v in item.items()if v is not None};entities.append(item);web['mainEntity']={'@id':item['@id']}
  if kind=='menu' and rows:
   entities.append({'@type':'ItemList','@id':url+'#items','numberOfItems':len(rows),'itemListElement':[{'@type':'ListItem','position':i+1,'name':p['name'],'url':self.origin+'/dish/'+p['id']+'/'}for i,p in enumerate(rows)]});web['mainEntity']={'@id':url+'#items'}
  crumbs=[{'@type':'ListItem','position':1,'name':'Wisteria cafe','item':self.origin+'/'}]
  if path!='/':
   if path.startswith('/dish/'):
    p=next(p for p in self.products if '/dish/'+p['id']+'/'==path)
    crumbs.append({'@type':'ListItem','position':2,'name':p['category'],'item':self.origin+self.category_path(p['category'])})
   crumbs.append({'@type':'ListItem','position':len(crumbs)+1,'name':title,'item':url})
   entities.append({'@type':'BreadcrumbList','@id':url+'#breadcrumbs','itemListElement':crumbs})
  return {'@context':'https://schema.org','@graph':entities}
 def render(self,path,title,description,body,attrs='',schema=None,header='',footer='',dialogs='',kind='page',rows=None,index=True,register_alias=True,social_image=None,extra_styles=None):
  pref=preferred(path);canonical=self.origin+pref;rows=rows or []
  if path.startswith('/dish/'):
   pid=path.strip('/').split('/')[1];title=self.product_titles[pid]+' — Севастополь';kind='dish'
   p=next(p for p in self.products if p['id']==pid);description=self.product_titles[pid]+'. '+plain(p.get('composition') or 'Состав и наличие уточните у кафе.')[:95]+f' Цена в меню {amount(p.get("priceFrom",p["price"]))}. Wisteria cafe, Севастополь.'
  title=re.sub(r'\s*\|\s*Wisteria cafe\s*$','',title,flags=re.I)
  full_title=title+' | Wisteria cafe';body=self.body_links(body);header=self.body_links(header);footer=self.body_links(footer)
  graph=self.graph(pref,plain(title),kind,schema,rows,social_image)
  image=(social_image or {}).get('src')or next((p['image']for p in rows if p.get('image')),None)or (schema or {}).get('image')or '/assets/d87f5e99f2f5761a.webp';image=asset_url(self.origin,image)
  image_meta=f'<meta property="og:image:width" content="{int(social_image["width"])}"><meta property="og:image:height" content="{int(social_image["height"])}"><meta property="og:image:alt" content="{E(social_image["alt"])}"><meta name="twitter:image" content="{E(image)}"><meta name="twitter:image:alt" content="{E(social_image["alt"])}">'if social_image else ''
  style_links=''.join('<link rel="stylesheet" href="'+E(path)+'">'for path in (extra_styles or []))
  verification=''.join(f'<meta name="{E(k)}" content="{E(v)}">' for k,v in self.verify.items()) if self.production else ''
  for actual in dict.fromkeys([pref,path]):
   actual_index=index and actual==pref and pref not in ['/politikakonfidentsialnosti','/404.html','/spasibo','/selfi','/primer']
   robots='index,follow,max-image-preview:large' if self.production and actual_index else 'noindex,follow'
   head=f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(full_title)}</title><meta name="description" content="{E(description)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{E(canonical)}"><meta property="og:type" content="{"article" if kind=="article" else "website"}"><meta property="og:locale" content="ru_RU"><meta property="og:site_name" content="Wisteria cafe"><meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(description)}"><meta property="og:url" content="{E(canonical)}"><meta property="og:image" content="{E(image)}"><meta name="twitter:card" content="summary_large_image">{verification}<link rel="icon" type="image/png" href="/assets/logo.png"><meta name="theme-color" content="#684177"><link rel="preload" href="/assets/fonts/NotoSerif-Regular.woff" as="font" type="font/woff" crossorigin><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/design.css?v=20261015-accents"><link rel="stylesheet" href="/experience.css"><link rel="stylesheet" href="/brand.css?v=20261015-accents"><script type="application/ld+json">{json.dumps(graph,ensure_ascii=False).replace("</","<\\/")}</script><script>window.WISTERIA_ANALYTICS={json.dumps({"enabled":self.production,"counterId":80581606})};</script><script defer src="/app.js"></script><script defer src="/experience.js?v=20261015-accents"></script><script defer src="/brand-nav.js?v=20261015-accents2"></script><script defer src="/analytics.js"></script>'
   head+=image_meta+style_links
   output=f'<!doctype html><html lang="ru"><head>{head}</head><body {attrs}>{header}<main id="main">{body}</main>{footer}{dialogs}</body></html>'
   f=file_for(self.output,actual);f.parent.mkdir(parents=True,exist_ok=True);f.write_text(output)
   self.pages[actual]={'path':actual,'canonical':canonical,'index':actual_index,'kind':kind}
   if actual!=pref and register_alias:self.redirects[actual]=pref
 def finish(self):
  # New review-Site paths and observed Tilda page-ID duplicates lead to one preferred URL.
  for source,target in PREFERRED.items():
   if target in self.pages and source not in self.redirects:self.add_redirect(source,target)
   for page_path in list(self.pages):
    if page_path.startswith(target.rstrip('/')+'/page/'):
     alias=source.rstrip('/')+page_path[len(target.rstrip('/')):]
     if alias!=page_path and alias not in self.redirects:self.add_redirect(alias,page_path)
  public=[v['canonical']for v in self.pages.values()if v['index'] and self.origin+v['path']==v['canonical']]
  sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(u)+'</loc></url>'for u in sorted(set(public)))+'</urlset>'
  (self.output/'sitemap.xml').write_text(sitemap)
  (self.output/'robots.txt').write_text('User-agent: *\nAllow: /\n'+('Sitemap: '+self.origin+'/sitemap.xml\n'if self.production else '# Preview: every HTML page has noindex; crawling is allowed so robots can read that rule.\n'))
  old=[]
  for p in self.source_inventory.get('pages',[]):
   path=p['sourcePath'];target=self.redirects.get(path,path);status=301 if path in self.redirects else 200 if path in self.pages else 'review'
   old.append({'path':path,'target':target,'status':status,'sourceHTTP':p.get('httpStatus'),'sourceTitle':p.get('title',''),'sourceIntent':p.get('pageIntent','')})
  manifest={'productionOrigin':PRODUCTION_ORIGIN,'previewOrigin':PREVIEW_ORIGIN,'profile':'production' if self.production else 'preview','pages':list(self.pages.values()),'redirects':[{'from':k,'to':v}for k,v in sorted(self.redirects.items())],'legacy':old}
  self.output.parent.mkdir(parents=True,exist_ok=True)
  out=self.output.parent/'seo-route-manifest.json' if self.production else self.root/'seo-route-manifest-preview.json';out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
  (self.output/'seo-route-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
  return manifest
 def add_redirect(self,source,target):
  if source==target:return
  if target not in self.pages:raise ValueError('Missing redirect target '+target)
  self.redirects[source]=target
  target_html=file_for(self.output,target).read_text()
  target_html=re.sub(r'<meta name="robots" content="[^"]*">','<meta name="robots" content="noindex,follow">',target_html,count=1)
  f=file_for(self.output,source);f.parent.mkdir(parents=True,exist_ok=True);f.write_text(target_html)
  self.pages[source]={'path':source,'canonical':self.origin+target,'index':False,'kind':'alias'}
