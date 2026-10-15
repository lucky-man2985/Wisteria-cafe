(()=>{
 const toggle=document.querySelector('.menu-toggle'),nav=document.querySelector('.navlinks');
 toggle?.addEventListener('click',()=>{const open=!nav.classList.contains('open');nav.classList.toggle('open',open);toggle.setAttribute('aria-expanded',String(open));});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){nav?.classList.remove('open');toggle?.setAttribute('aria-expanded','false');}});
 function toast(message){document.querySelector('.toast')?.remove();const item=document.createElement('div');item.className='toast';item.setAttribute('role','status');item.textContent=message;document.body.append(item);setTimeout(()=>item.remove(),4200);}
 document.querySelectorAll('[data-demo]').forEach(item=>item.addEventListener('click',()=>toast(item.dataset.demo)));
 const cards=[...document.querySelectorAll('.catalog-main .product-card')];let category='Всё меню';
 const search=document.querySelector('input[type=search]'),only=document.querySelector('.favorites-only');
 const filter=()=>{let count=0;cards.forEach(card=>{card.hidden=!((category==='Всё меню'||card.dataset.category===category)&&(!search.value||card.dataset.name.includes(search.value.toLowerCase()))&&(!only.checked||card.querySelector('.favorite').getAttribute('aria-pressed')==='true'));if(!card.hidden)count++;});if(!cards.length)return;document.querySelector('.empty-result').hidden=count!==0;document.querySelector('.result-count').textContent=search.value||category!=='Всё меню'||only.checked?`Найдено: ${count}`:'В меню 431 позиция';};
 search?.addEventListener('input',filter);only?.addEventListener('change',filter);
 document.querySelectorAll('.favorite').forEach(button=>button.addEventListener('click',()=>{const active=button.getAttribute('aria-pressed')!=='true';button.setAttribute('aria-pressed',String(active));button.setAttribute('aria-label',active?'Убрать из избранного':'Добавить в избранное');if(cards.length)filter();}));
 document.querySelector('.filter-toggle')?.addEventListener('click',event=>{const panel=document.querySelector('.filter-panel');panel.hidden=!panel.hidden;event.currentTarget.setAttribute('aria-expanded',String(!panel.hidden));});
 document.querySelectorAll('[data-filter-category]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();category=link.dataset.filterCategory;document.querySelectorAll('[data-filter-category]').forEach(item=>item.classList.toggle('active',item===link));filter();}));
 document.querySelector('.sort')?.addEventListener('change',event=>{const rows=[...cards];if(event.target.value!=='default')rows.sort((a,b)=>(Number(a.dataset.price)-Number(b.dataset.price))*(event.target.value==='up'?1:-1));const grid=document.querySelector('.catalog-main .product-grid');rows.forEach(row=>grid.append(row));});
})();
