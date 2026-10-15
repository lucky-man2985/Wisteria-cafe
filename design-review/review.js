document.querySelectorAll('.favorite').forEach(button=>button.addEventListener('click',()=>{const saved=button.getAttribute('aria-pressed')!=='true';button.setAttribute('aria-pressed',String(saved));button.setAttribute('aria-label',saved?'Убрать из избранного':'Добавить в избранное');button.classList.toggle('is-saved',saved);}));
document.querySelectorAll('.segmented').forEach(group=>group.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{group.querySelectorAll('button').forEach(item=>{item.classList.toggle('selected',item===button);item.setAttribute('aria-pressed',String(item===button));});})));
const drawer=document.querySelector('.mobile-drawer');document.querySelector('.mobile-nav').addEventListener('click',e=>{drawer.hidden=!drawer.hidden;e.currentTarget.setAttribute('aria-expanded',String(!drawer.hidden));});
const dialog=document.querySelector('#cart-dialog');document.querySelector('[data-open-cart]').addEventListener('click',()=>dialog.showModal());document.querySelector('[data-close-dialog]').addEventListener('click',()=>dialog.close());
document.querySelector('.filter-btn')?.addEventListener('click',e=>{const panel=document.querySelector('.filter-panel');panel.hidden=!panel.hidden;e.currentTarget.setAttribute('aria-expanded',String(!panel.hidden));});
const search=document.querySelector('input[type=search]');search?.addEventListener('input',()=>{let count=0;document.querySelectorAll('.food-card').forEach(card=>{card.hidden=!card.textContent.toLowerCase().includes(search.value.toLowerCase());if(!card.hidden)count++;});document.querySelector('.empty-search').hidden=count!==0;document.querySelector('.item-count').textContent=search.value?`Найдено в макете: ${count}`:document.body.dataset.page==='desserts'?'Десерты в меню':'431 позиций в меню';});
document.querySelectorAll('[data-qty]').forEach(button=>button.addEventListener('click',()=>{const output=document.querySelector('.quantity output');output.value=String(Math.max(1,Math.min(99,Number(output.value)+Number(button.dataset.qty))));}));
function toast(message){document.querySelector('.toast')?.remove();const note=document.createElement('div');note.className='toast';note.setAttribute('role','status');note.textContent=message;document.body.append(note);setTimeout(()=>note.remove(),4500);}
document.querySelector('[data-add-demo]')?.addEventListener('click',()=>toast('Макет: выбранное состояние. Заказ не отправлен.'));
document.querySelector('[data-more]')?.addEventListener('click',()=>toast('В макете показана часть меню. Полный каталог — в действующей версии сайта.'));
const activeCategory=document.querySelector('.sidebar nav a.active');if(activeCategory&&matchMedia('(max-width:760px)').matches){const scroller=activeCategory.parentElement;scroller.scrollLeft=activeCategory.offsetLeft-22;}
const quick=document.querySelector('#quick-dialog');
document.querySelector('[data-close-quick]').addEventListener('click',()=>quick.close());
let menuData;
function element(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;}
document.querySelectorAll('a[href*="product.html?item="]').forEach(link=>link.addEventListener('click',async event=>{
 event.preventDefault();
 menuData??=await fetch('review-data.json').then(r=>r.json());
 const id=new URL(link.href).searchParams.get('item'),product=menuData.find(p=>p.id===id);if(!product)return;
 quick.querySelector('h2').textContent=product.name;
 const body=quick.querySelector('.quick-body');body.replaceChildren();
 const img=element('img');img.src=product.image.replace(/^\//,'');img.alt=product.name;body.append(img);
 body.append(element('p',`${product.category} · ${product.weight||''}`));
 body.append(element('p',product.composition||'Полный состав уточните у сотрудника кафе.'));
 for(const option of product.options||[]){const label=element('label',option.name);const select=element('select');for(const value of option.values)select.append(element('option',value));label.append(select);body.append(label);}
 body.append(element('strong',`${product.optionPrices?.length?'от ':''}${product.priceFrom??product.price} ₽`,'price'));
 body.append(element('p','По составу: '+(product.allergens?.join(', ')||'аллергены требуют уточнения')+'. Состав выбранных добавок подтвердит кафе.'));
 for(const issue of product.sourceIssues||[])body.append(element('p',issue,'notice'));
 body.append(element('p','Визуальный макет. Цена и наличие подтверждаются кафе; заказ не отправляется.','notice'));
 quick.showModal();
}));
