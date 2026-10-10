/* AZA FLOWERS — docs/ static versiya, ciello.uz layout 1:1. data.json dan o'qiydi. */
'use strict';
const $=s=>document.querySelector(s);
let ALL=[],CATS=[],CFG={delivery_note:'',contact:{}},curCat='all',curTab='new';
let cart={}; try{cart=JSON.parse(localStorage.getItem('aza_cart')||'{}')}catch(e){cart={}}
let wish=new Set(JSON.parse(localStorage.getItem('aza_wish')||'[]'));
const fmt=n=>(Number(n)||0).toLocaleString('uz-UZ').replace(/,/g,' ')+" so'm";
function toast(m){const t=$('#toast');if(!t)return;t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),2600)}

const U=(id,w=800)=>`https://images.unsplash.com/${id}?q=80&w=${w}&auto=format&fit=crop`;
const LOCAL_BUKET='./uploads/mavsumiy-aralash-buket_1791556816.jpg';
const PHOTOS={buketlar:LOCAL_BUKET,atirgullar:U('photo-1518895949257-7621c3c786d7'),kompozitsiyalar:U('photo-1508610048659-a06b669e3321'),sovgalar:U('photo-1526047932273-341f2a7631f9'),xonalar:U('photo-1485955900006-10f4d324d411'),toy:U('photo-1522673607200-164d1b6ce486')};
const BY_SLUG={'million-atirgul':U('photo-1518895949257-7621c3c786d7'),'qizil-atirgul-25':U('photo-1494972308805-463bc619d34e'),'oq-atirgul-kompozitsiya':U('photo-1508610048659-a06b669e3321'),'pushti-lolalar':U('photo-1520763185298-1b434c919102'),'bahor-savati':U('photo-1526047932273-341f2a7631f9'),'kungaboqar-quvonchi':U('photo-1470509037663-253afd7f0f51'),'pionlar-nafosati':U('photo-1591886960571-74d43a9d4166'),'orkide-kompozitsiya':U('photo-1610397648930-477b8c7f0943'),'shokolad-atirgul-sovga':U('photo-1549007994-cb92caebd54b'),'toy-buketi-oq-bulut':U('photo-1522673607200-164d1b6ce486'),'fikus-xona-uchun':U('photo-1485955900006-10f4d324d411'),'sukkulentlar-toplami':U('photo-1459156212016-c812468e2115'),'gul-barglari-yolagi':U('photo-1490750967868-88aa4486c946'),'mavsumiy-aralash-buket':U('photo-1490750967868-88aa4486c946')};
function imgFor(p){let ph=p.photo||'';if(ph.startsWith('/static/uploads/'))ph='.'+ph.replace('/static','');if(ph.startsWith('/static/'))ph='.'+ph;if(ph)return ph;return BY_SLUG[p.slug]||PHOTOS[p.category]||PHOTOS.buketlar}
function flowerImg(p){const src=imgFor(p);const esc=(p.name||'').replace(/"/g,'');return `<img src="${src}" alt="${esc}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block" onerror="this.onerror=null;this.src='${PHOTOS.buketlar}'">`}
function badges(p){let b='';if(p.discount_pct)b+=`<span class="td">-${p.discount_pct}%</span>`;if(p.is_featured===1)b+=`<span class="tt">Top</span>`;if(p.is_featured===2)b+=`<span class="tn">Yangi</span>`;return `<div class="tag">${b}</div>`}
function card(p){
  const cat=(CATS.find(c=>c.slug===p.category)||{}).name||p.category;
  return `<div class="card"><div class="imgw" data-view="${p.slug}">${flowerImg(p)}${badges(p)}<button class="wish ${wish.has(p.slug)?'on':''}" data-wish="${p.slug}">${wish.has(p.slug)?'♥':'♡'}</button><button class="quick" data-add="${p.slug}" ${p.stock<=0?'disabled style="opacity:.4"':''}>${p.stock>0?'Savatga qo‘shish':'Tugadi'}</button></div>
  <div class="pbody"><div class="cat">${cat}</div><div class="name" data-view="${p.slug}">${p.name}</div><div class="stars">★★★★★ <span>4.9 (120+)</span></div>
  <div class="prow"><span class="price">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div></div></div>`;
}
async function load(){
  const d=await (await fetch('./data.json')).json();
  CFG={delivery_note:d.delivery_note,contact:d.contact};
  CATS=d.categories.map(c=>({...c,total:d.products.filter(p=>p.category===c.slug).length}));
  ALL=d.products;
  $('#cfgLine').textContent=`${ALL.length} mahsulot • Yandex orqali 3 soatgacha yetkazish`;
  $('#delText').textContent=(CFG.delivery_note||'')+' Har kuni 08:00–22:00.';
  const c=CFG.contact||{};
  if(c.phones&&c.phones[0]){$('#hPhone').textContent=c.phones[0];$('#hPhone2').textContent=c.phones[0]}
  const phones=(c.phones||[]).map(p=>`<a href="tel:${p.replace(/\s/g,'')}" style="font-weight:600">${p}</a>`).join(', ');
  $('#contactBox').innerHTML=`Telefonlar: ${phones}<br>Manzil: ${c.address||''}<br>Ish vaqti: ${c.hours||''}`;
  $('#footContact').innerHTML=(c.phones||[]).map(p=>`<div class="frow"><div><a href="tel:${p.replace(/\s/g,'')}">${p}</a></div></div>`).join('')+`<div class="frow"><div>${c.address||''}</div></div><div class="frow"><div>${c.hours||''}</div></div>`;
  $('#tgBtn').href=c.telegram||'#';$('#insBtn').href=c.instagram||'#';
  $('#tgBtnF').href=c.telegram||'#';$('#insBtnF').href=c.instagram||'#';
  $('#socTg').href=c.telegram||'#';$('#socIg').href=c.instagram||'#';
  renderPills();refresh(true);renderTabs();
}
function renderPills(){$('#pills').innerHTML=[{slug:'all',name:'Barchasi'},...CATS].map(c=>`<button class="pill ${curCat===c.slug?'on':''}" data-cat="${c.slug}">${c.name}</button>`).join('')}
function renderCircles(){
  const box=$('#catCircles');if(!box)return;
  box.innerHTML=CATS.map(c=>{
    const rep=ALL.find(p=>p.category===c.slug)||{name:c.name,slug:c.slug,photo:PHOTOS[c.slug]};
    return `<div class="catcircle" data-cat="${c.slug}"><div class="im"><div>${flowerImg(rep)}</div></div><b>${c.name}</b><small>${c.total||''} mahsulot</small></div>`;
  }).join('');
  box.onclick=e=>{const el=e.target.closest('[data-cat]');if(!el)return;curCat=el.dataset.cat;renderPills();refresh();document.getElementById('katalog').scrollIntoView({behavior:'smooth'})};
}
function renderTabs(){
  let list=[...ALL];
  if(curTab==='new')list=list.filter(p=>p.is_featured===2||p.is_featured===1).slice(0,12);
  else if(curTab==='hit')list=list.filter(p=>p.is_featured===1).slice(0,12);
  else list=list.filter(p=>p.discount_pct>0).slice(0,12);
  if(!list.length)list=ALL.slice(0,12);
  $('#tabGrid').innerHTML=list.map(card).join('')||`<div class="empty">Hozircha bo'sh</div>`;
  bindCards();
}
function refresh(first){
  const q=($('#q').value||'').trim().toLowerCase(),sort=$('#sort').value;
  let list=[...ALL];
  if(curCat!=='all')list=list.filter(p=>p.category===curCat);
  if(q)list=list.filter(p=>p.name.toLowerCase().includes(q)||(p.description||'').toLowerCase().includes(q));
  if(sort==='cheap')list.sort((a,b)=>a.price-b.price);
  else if(sort==='expensive')list.sort((a,b)=>b.price-a.price);
  else if(sort==='discount')list.sort((a,b)=>(b.discount_pct||0)-(a.discount_pct||0));
  else list.sort((a,b)=>((-b.is_featured)-(-a.is_featured))||(a.price-b.price));
  $('#grid').innerHTML=list.map(card).join('')||`<div class="empty">Hech narsa topilmadi</div>`;
  $('#count').textContent=q?`"${q}" — ${list.length} ta topildi`:list.length+' ta topildi';
  if(first){
    renderCircles();
    const hb1=ALL.filter(p=>p.is_featured===1)[0]||ALL[0];
    const hb2=ALL.filter(p=>p.category==='toy')[0]||ALL[1]||ALL[0];
    if(hb1)$('#heroVis').innerHTML=flowerImg(hb1);
    if(hb2&&$('#heroVis2'))$('#heroVis2').innerHTML=flowerImg(hb2);
    const feat=ALL.filter(p=>p.is_featured===2)[0]||ALL[2]||ALL[0];
    if(feat&&$('#featImg'))$('#featImg').innerHTML=flowerImg(feat);
    document.querySelectorAll('[data-bannerbg]').forEach((el,i)=>{
      const p=ALL.filter(x=>x.discount_pct>0)[i]||ALL[i]||ALL[0];
      if(p)el.innerHTML=flowerImg(p);
    });
    renderTabs();initSlider();
  }
  bindCards();paintWish();
}
function bindCards(){
  document.querySelectorAll('[data-add]').forEach(b=>b.onclick=e=>{e.stopPropagation();if(!b.disabled)add(b.dataset.add)});
  document.querySelectorAll('[data-view]').forEach(el=>{el.onclick=e=>{if(e.target.closest('[data-wish]')||e.target.closest('[data-add]'))return;view(el.dataset.view)}});
  document.querySelectorAll('[data-wish]').forEach(b=>b.onclick=e=>{e.stopPropagation();toggleWish(b.dataset.wish)});
}
function toggleWish(slug){
  if(wish.has(slug)){wish.delete(slug)}else{wish.add(slug);toast('Sevimlilarga qo‘shildi ♥')}
  localStorage.setItem('aza_wish',JSON.stringify([...wish]));
  document.querySelectorAll(`[data-wish="${slug}"]`).forEach(b=>{b.classList.toggle('on',wish.has(slug));b.textContent=wish.has(slug)?'♥':'♡'});
  paintWish();
}
function paintWish(){const n=wish.size,el=$('#wishN');if(!el)return;el.style.display=n?'grid':'none';el.textContent=n}
function add(slug,n=1){const p=ALL.find(x=>x.slug===slug)||window._cur;if(!p)return;cart[slug]=Math.min(p.stock,(cart[slug]||0)+n);localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart();toast('Savatga qo‘shildi')}
function cartItems(){return Object.entries(cart).map(([slug,qty])=>{const p=ALL.find(x=>x.slug===slug);return p?{...p,qty}:null}).filter(Boolean)}
function renderCart(){
  const items=cartItems(),n=items.reduce((a,i)=>a+i.qty,0);$('#cartN').textContent=n;
  if(!items.length){$('#cartBody').innerHTML=`<div class="empty">Savat bo'sh<br><a href="#katalog" class="btn btn-acc" style="margin-top:12px;display:inline-block" onclick="closeDrawer()">Gul tanlash</a></div>`;$('#cartFoot').innerHTML='';return}
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  $('#cartBody').innerHTML=items.map(i=>`<div class="citem">${flowerImg(i)}<div><b style="font-size:13px">${i.name}</b><div style="color:var(--muted);font-size:13px">${fmt(i.price)}</div><div class="qty"><button onclick="chQty('${i.slug}',-1)">−</button><b>${i.qty}</b><button onclick="chQty('${i.slug}',1)">+</button></div></div><button class="pill" onclick="rm('${i.slug}')">✕</button></div>`).join('')
    +`<div style="border:1px dashed var(--accent-dark);padding:10px 12px;font-size:13px;color:var(--muted)">✦ ${CFG.delivery_note||"Yetkazish Yandex'ga alohida to'lanadi"}</div>`;
  $('#cartFoot').innerHTML=`<div class="row"><span>Gullar summasi:</span><b>${fmt(sub)}</b></div><div class="row"><span>Yetkazish:</span><b>Yandex alohida</b></div><div class="row ttl"><span>Jami:</span><span>${fmt(sub)}</span></div><button class="btn btn-acc" style="width:100%;margin-top:8px" onclick="openCheckout()">Buyurtma berish →</button>`;
}
window.chQty=(s,d)=>{const p=ALL.find(x=>x.slug===s);cart[s]=(cart[s]||0)+d;if(cart[s]<=0)delete cart[s];if(p&&cart[s]>p.stock)cart[s]=p.stock;localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
window.rm=s=>{delete cart[s];localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
function view(slug){
  const p=ALL.find(x=>x.slug===slug);if(!p)return;window._cur=p;
  const rel=ALL.filter(x=>x.category===p.category&&x.slug!==p.slug).slice(0,4);
  const cat=(CATS.find(c=>c.slug===p.category)||{}).name||'';
  $('#pmImg').innerHTML=flowerImg(p)+badges(p);
  $('#pmBody').innerHTML=`<div class="cat">${cat}</div><h2>${p.name}</h2><div class="stars">★★★★★ <span>4.9 (120+)</span></div><p style="color:var(--body);line-height:1.6">${p.description||''}</p><div class="prow"><span class="price" style="font-size:24px">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div><div class="form"><div class="qty"><button onclick="mQty(-1)">−</button><b id="mq">1</b><button onclick="mQty(1)">+</button><span style="color:var(--muted);font-size:13px">Omborda: ${p.stock}</span></div><button class="btn btn-acc" style="width:100%" onclick="add('${p.slug}',+document.querySelector('#mq').textContent);closeModal('#pmodal')">Savatga qo'shish</button></div>${rel.length?`<h3 style="font-family:var(--serif);font-size:22px;font-weight:400;margin:16px 0 10px">Tavsiya etamiz:</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${rel.map(r=>`<div style="border:1px solid var(--line);cursor:pointer" onclick="view('${r.slug}')">${flowerImg(r)}<div style="padding:8px;font-size:12px">${r.name}<br><b>${fmt(r.price)}</b></div></div>`).join('')}</div>`:''}`;
  openModal('#pmodal');
}
window.mQty=d=>{const e=$('#mq');e.textContent=Math.max(1,Math.min(20,+e.textContent+d))};
window.toggleWish=toggleWish;window.add=add;window.view=view;
function openModal(s){$(s).classList.add('show');$('#overlay').classList.add('show')}
function closeModal(s){$(s).classList.remove('show');if(!$('#drawer').classList.contains('show'))$('#overlay').classList.remove('show')}
window.closeModal=closeModal;
function openDrawer(){$('#drawer').classList.add('show');$('#overlay').classList.add('show');renderCart()}
function closeDrawer(){$('#drawer').classList.remove('show');$('#overlay').classList.remove('show')}
window.closeDrawer=closeDrawer;
window.openCheckout=()=>{const items=cartItems();if(!items.length)return;const sub=items.reduce((a,i)=>a+i.price*i.qty,0);$('#sumLine').textContent=`${items.length} tur • Gullar: ${fmt(sub)}. Yetkazish Yandex'ga alohida to'lanadi.`;closeDrawer();openModal('#cmodal')};
let curSlide=0,slideTimer=null;
function showSlide(i){const slides=document.querySelectorAll('.slide');if(!slides.length)return;curSlide=(i+slides.length)%slides.length;slides.forEach((s,k)=>s.classList.toggle('on',k===curSlide));document.querySelectorAll('#slideDots button').forEach((d,k)=>d.classList.toggle('on',k===curSlide))}
function initSlider(){const slides=document.querySelectorAll('.slide');const dots=$('#slideDots');if(dots&&!dots.innerHTML)dots.innerHTML=[...slides].map((_,k)=>`<button data-dot="${k}" class="${k===0?'on':''}"></button>`).join('');dots.onclick=e=>{const b=e.target.closest('[data-dot]');if(b){showSlide(+b.dataset.dot);restartAuto()}};$('#slidePrev').onclick=()=>{showSlide(curSlide-1);restartAuto()};$('#slideNext').onclick=()=>{showSlide(curSlide+1);restartAuto()};restartAuto()}
function restartAuto(){clearInterval(slideTimer);slideTimer=setInterval(()=>showSlide(curSlide+1),5000)}
$('#openCart').onclick=openDrawer;$('#closeCart').onclick=closeDrawer;
$('#overlay').onclick=()=>{closeDrawer();document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'));$('#mmenu').classList.remove('show')};
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'));if(!$('#drawer').classList.contains('show'))$('#overlay').classList.remove('show')});
$('#burger').onclick=()=>{$('#mmenu').classList.add('show');$('#overlay').classList.add('show')};
$('#mmenuX').onclick=()=>{$('#mmenu').classList.remove('show');$('#overlay').classList.remove('show')};
document.querySelectorAll('#mmenu [data-navcat]').forEach(a=>a.onclick=()=>{curCat=a.dataset.navcat;renderPills();refresh();$('#mmenu').classList.remove('show');$('#overlay').classList.remove('show')});
$('#searchBtn').onclick=()=>{$('#searchOv').classList.add('show');setTimeout(()=>$('#q').focus(),50)};
$('#searchX').onclick=()=>$('#searchOv').classList.remove('show');
$('#pills').onclick=e=>{if(e.target.dataset.cat){curCat=e.target.dataset.cat;renderPills();refresh()}};
document.querySelectorAll('.tabbtn').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabbtn').forEach(x=>x.classList.remove('on'));b.classList.add('on');curTab=b.dataset.tab;renderTabs()});
document.querySelectorAll('[data-navcat]').forEach(a=>{if(a.closest('#mmenu'))return;a.onclick=()=>{curCat=a.dataset.navcat;renderPills();refresh()}});
$('#mainNav').onclick=e=>{const a=e.target.closest('[data-navcat]');if(a){curCat=a.dataset.navcat;renderPills();refresh()}};
$('#sort').onchange=()=>refresh();
$('#q').addEventListener('input',()=>{clearTimeout(window._qt);window._qt=setTimeout(()=>refresh(),300)});
$('#q').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();refresh();$('#searchOv').classList.remove('show');document.getElementById('katalog').scrollIntoView()}});
$('#wishBtn').onclick=()=>{if(!wish.size)return toast('Sevimlilar bo‘sh — ♡ bosing');const list=ALL.filter(p=>wish.has(p.slug));$('#grid').innerHTML=list.map(card).join('');bindCards();document.getElementById('katalog').scrollIntoView({behavior:'smooth'})};
$('#sendOrder').onclick=()=>{
  const name=$('#fName').value.trim(),phone=$('#fPhone').value.trim(),addr=$('#fAddr').value.trim(),com=$('#fCom').value.trim();
  const items=cartItems();
  if(name.length<2)return toast('Ismingizni yozing');if(phone.length<7)return toast('Telefonni yozing');if(addr.length<5)return toast('Manzilni yozing');if(!items.length)return toast('Savat bo‘sh');
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  const lines=items.map(i=>`• ${i.name} — ${i.qty} dona — ${fmt(i.price*i.qty)}`).join('\n');
  const msg=`🌷 AZA FLOWERS — yangi buyurtma (sayt)\n👤 ${name}\n📞 ${phone}\n📍 ${addr}\n💬 ${com||'-'}\n\n${lines}\n\nJami: ${fmt(sub)}\nYetkazish: Yandex alohida`;
  try{navigator.clipboard.writeText(msg).catch(()=>{})}catch(e){}
  window.open((CFG.contact&&CFG.contact.telegram)||'https://t.me/azaflowers','_blank');
  cart={};localStorage.setItem('aza_cart','{}');renderCart();closeModal('#cmodal');
  toast('Buyurtma matni nusxalandi — Telegramda yuboring 🌷');
};
load().then(()=>{renderCart();paintWish()}).catch(()=>toast("Ma'lumot yuklanmadi"));
