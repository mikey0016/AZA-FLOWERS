/* FAX Flores — umumiy frontend (barcha sahifalar uchun) */
const $=s=>document.querySelector(s);
const on=(sel,ev,fn)=>{const el=typeof sel==='string'?document.querySelector(sel):sel;if(el)el.addEventListener(ev,fn);return el};
let ALL=[],CATS=[],CFG={delivery_fee:0,free_delivery_from:null,delivery_note:'',contact:{}},curCat='all',curTab='new';
let cart={}; try{cart=JSON.parse(localStorage.getItem('aza_cart')||'{}')}catch(e){cart={}}
let wish=new Set(JSON.parse(localStorage.getItem('aza_wish')||'[]'));
const fmt=n=>(Number(n)||0).toLocaleString('uz-UZ').replace(/,/g,' ')+" so'm";
function toast(m){const t=$('#toast');if(!t)return;t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),2600)}
let ME=null;
const BOT_USERNAME='azaflowersbot';
const SHIP_LABEL={standard:'Standart (Yandex, 3 soat)',express:'Tezkor (1 soat)'};
const PAY_LABEL={cash:"Naqd / yetkazib berishda",card:'Plastik karta (terminal)',online:"Online to'lov (Click / Payme)"};
function authHeaders(){const t=localStorage.getItem('aza_token');return t?{'Authorization':'Bearer '+t}:{}}
async function loadMe(){const t=localStorage.getItem('aza_token');if(!t)return null;try{const r=await fetch('/api/auth/me',{headers:authHeaders()});if(!r.ok){localStorage.removeItem('aza_token');localStorage.removeItem('aza_user');return null}ME=await r.json();localStorage.setItem('aza_user',JSON.stringify(ME));return ME}catch(e){return null}}
function paintAuth(){const el=$('#authArea');if(!el)return;if(ME){el.innerHTML=`<a class="pill" href="/cabinet">${escA(ME.name.split(' ')[0])} → Kabinet</a>`}else{el.innerHTML=`<button class="iconbtn" id="liBtn" title="Kirish" style="font-size:20px">👤</button>`;on('#liBtn','click',()=>openModal('#amodal'))}}
function switchTab(w){const a=$('#tabLogin'),b=$('#tabReg');if(!a||!b)return;a.classList.toggle('on',w==='login');b.classList.toggle('on',w==='reg');$('#paneLogin').style.display=w==='login'?'grid':'none';$('#paneReg').style.display=w==='reg'?'grid':'none'}
async function doAuth(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){toast('Xatolik: '+(d.detail||'qayta urining'));return}localStorage.setItem('aza_token',d.token);localStorage.setItem('aza_user',JSON.stringify(d.user));ME=d.user;paintAuth();closeModal('#amodal');toast(`Xush kelibsiz, ${ME.name}!`)}
function escA(s){return String(s||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}

function flowerSVG(p,w=400,h=400){
  if(p.photo)return `<div style="aspect-ratio:${w}/${h};overflow:hidden;background:var(--imgbg)"><img src="${p.photo}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block"></div>`;
  const o=p.img||{petals:12,petal:'#c9a24f',center:'#f6e3a5',bg:['#faf5ec','#efe0c3'],leaves:true};
  const cx=w/2,cy=h/2-10,R=Math.min(w,h)*0.30;let s='';
  for(let i=0;i<o.petals;i++){const a=i/o.petals*Math.PI*2;
    const x=cx+Math.cos(a)*R*0.62,y=cy+Math.sin(a)*R*0.62;
    s+=`<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="${(R*0.42).toFixed(1)}" ry="${(R*0.24).toFixed(1)}" fill="${o.petal}" opacity=".95" transform="rotate(${(a*180/Math.PI).toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})"/>`}
  let lv=o.leaves?`<path d="M${cx-70} ${h-30} Q ${cx-30} ${h-90} ${cx-8} ${cy+40} Q ${cx-50} ${h-60} ${cx-70} ${h-30}Z" fill="#7ba889"/><path d="M${cx+70} ${h-30} Q ${cx+30} ${h-90} ${cx+8} ${cy+40} Q ${cx+50} ${h-60} ${cx+70} ${h-30}Z" fill="#93bfa3"/>`:'';
  return `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g${p.slug}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${o.bg[0]}"/><stop offset="1" stop-color="${o.bg[1]}"/></linearGradient></defs><rect width="${w}" height="${h}" fill="url(#g${p.slug})"/>${lv}${s}<circle cx="${cx}" cy="${cy}" r="${(R*0.34).toFixed(1)}" fill="${o.center}"/><circle cx="${cx-R*0.1}" cy="${cy-R*0.12}" r="${(R*0.07).toFixed(1)}" fill="#ffffffaa"/></svg>`;
}
function badges(p){
  let b='';
  if(p.discount_pct)b+=`<span class="td">-${p.discount_pct}%</span>`;
  if(p.is_featured===1)b+=`<span class="tt">Top</span>`;
  if(p.is_featured===2)b+=`<span class="tn">Yangi</span>`;
  return `<div class="tag">${b}</div>`;
}
function card(p){
  const cat=(CATS.find(c=>c.slug===p.category)||{}).name||p.category;
  return `<div class="card"><div class="imgw" data-link="/product/${p.slug}">${flowerSVG(p)}${badges(p)}<button class="wish ${wish.has(p.slug)?'on':''}" data-wish="${p.slug}">${wish.has(p.slug)?'♥':'♡'}</button><button class="quick" data-add="${p.slug}" ${p.stock<=0?'disabled style="opacity:.4"':''}>${p.stock>0?'Savatga qo‘shish':'Tugadi'}</button></div>
  <div class="pbody"><div class="cat">${cat}</div><div class="name" data-link="/product/${p.slug}">${p.name}</div><div class="stars">★★★★★ <span>4.9 (120+)</span></div>
  <div class="prow"><span class="price">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div></div></div>`;
}

/* ---------- chrome ---------- */
async function load(){
  const [cfg,cats]=await Promise.all([(await fetch('/api/config')).json(),(await fetch('/api/categories')).json()]);
  CFG=cfg;CATS=cats;
  const total=cats.reduce((a,c)=>a+c.total,0);
  const cl=$('#cfgLine');if(cl)cl.textContent=`${total} mahsulot • Yandex orqali 3 soatgacha yetkazish`;
  const dt=$('#delText');if(dt)dt.textContent=(cfg.delivery_note||'')+' Har kuni 08:00–22:00.';
  const c=cfg.contact||{};
  const ph=(c.phones||[])[0]||'+998 90 350 71 78';
  const h1=$('#hPhone');if(h1)h1.textContent=ph;
  const h2=$('#hPhone2');if(h2)h2.textContent=ph;
  const team=c.team||(c.admins||[]).map(a=>({role:'Admin',handle:a,url:'https://t.me/'+a.replace('@',''),phone:''}));
  const phLink=m=>m.phone?` · <a href="tel:${m.phone.replace(/\s/g,'')}" style="font-weight:600">${m.phone}</a>`:'';
  const teamLinks=team.map(m=>`${m.role}: <a href="${m.url}" target="_blank" style="color:var(--accent-dark);font-weight:600">${m.handle}</a>${phLink(m)}`).join('<br>');
  const phones=(c.phones||[]).map(p=>`<a href="tel:${p.replace(/\s/g,'')}" style="font-weight:600">${p}</a>`).join(', ');
  const cb=$('#contactBox');if(cb)cb.innerHTML=`Telefonlar: ${phones}<br>Manzil: ${c.address||''}<br>Ish vaqti: ${c.hours||''}<br>${teamLinks}`;
  const fc=$('#footContact');if(fc)fc.innerHTML=(c.phones||[]).map(p=>`<div class="frow"><div><a href="tel:${p.replace(/\s/g,'')}">${p}</a></div></div>`).join('')+`<div class="frow"><div>${c.address||''}</div></div><div class="frow"><div>${c.hours||''}</div></div>`+team.map(m=>`<div class="frow"><div>${m.role}: <a href="${m.url}" target="_blank">${m.handle}</a>${phLink(m)}</div></div>`).join('');
  const fcat=$('#footCats');if(fcat)fcat.innerHTML=cats.map(x=>`<a href="/shop?cat=${x.slug}">${x.name}</a>`).join('');
  for(const id of ['tgBtn','tgBtnF','socTg','tgFloat']) {const e=document.getElementById(id);if(e)e.href=c.telegram||'#'}
  for(const id of ['insBtn','insBtnF','socIg']) {const e=document.getElementById(id);if(e)e.href=c.instagram||'#'}
  const qp=new URLSearchParams(location.search);
  if(qp.get('cat'))curCat=qp.get('cat');
  if(qp.get('sort'))curCat=curCat; // sort alohida
  if($('#pills')){renderPills();const s=$('#sort');if(s&&qp.get('sort'))s.value=qp.get('sort');const q=$('#q');if(q&&qp.get('q'))q.value=qp.get('q');await refresh(true)}
  if($('#tabGrid')){await ensureProducts();renderTabs()}
  if($('#catCircles')){await ensureProducts();renderCircles();paintHero()}
  if($('#wishGrid')){await ensureProducts();renderWishPage()}
  if($('#pDetail'))initProductPage();
  if($('#coBody')){await ensureProducts();renderCheckout()}
}
async function ensureProducts(){
  if(ALL.length)return;
  try{ALL=(await (await fetch('/api/products?sort=popular')).json())}catch(e){ALL=[]}
}
function paintHero(){
  if(!ALL.length)return;
  const hb1=ALL.filter(p=>p.is_featured===1)[0]||ALL[0];
  const hb2=ALL.filter(p=>p.category==='toy')[0]||ALL[1]||ALL[0];
  const e1=$('#heroVis');if(e1&&hb1)e1.innerHTML=flowerSVG(hb1,600,520);
  const e2=$('#heroVis2');if(e2&&hb2)e2.innerHTML=flowerSVG(hb2,600,520);
  const feat=ALL.filter(p=>p.is_featured===2)[0]||ALL[2]||ALL[0];
  const ef=$('#featImg');if(ef&&feat)ef.innerHTML=flowerSVG(feat,500,500);
  document.querySelectorAll('[data-bannerbg]').forEach((el,i)=>{
    const p=ALL.filter(x=>x.discount_pct>0)[i]||ALL[i]||ALL[0];
    if(p)el.innerHTML=flowerSVG(p,500,340);
  });
  initSlider();
}

/* ---------- katalog ---------- */
function renderPills(){
  const box=$('#pills');if(!box)return;
  const sale=document.body.dataset.sale==='1';
  box.innerHTML=[{slug:'all',name:'Barchasi'},...CATS].map(c=>`<button class="pill ${curCat===c.slug?'on':''}" data-cat="${c.slug}">${c.name}</button>`).join('');
}
function renderCircles(){
  const box=$('#catCircles');if(!box)return;
  box.innerHTML=CATS.map(c=>{
    const rep=ALL.find(p=>p.category===c.slug)||{slug:c.slug,img:{petals:12,petal:'#c9a24f',center:'#f6e3a5',bg:['#faf5ec','#efe0c3'],leaves:true}};
    return `<div class="catcircle" data-cat="${c.slug}"><div class="im"><div>${flowerSVG(rep,200,200)}</div></div><b>${c.name}</b><small>${c.total||''} mahsulot</small></div>`;
  }).join('');
  box.onclick=e=>{const el=e.target.closest('[data-cat]');if(!el)return;location.href='/shop?cat='+el.dataset.cat};
}
function renderTabs(){
  const box=$('#tabGrid');if(!box)return;
  let list=[...ALL];
  if(curTab==='new')list=list.filter(p=>p.is_featured===2||p.is_featured===1).slice(0,12);
  else if(curTab==='hit')list=list.filter(p=>p.is_featured===1).slice(0,12);
  else list=list.filter(p=>p.discount_pct>0).slice(0,12);
  if(!list.length)list=ALL.slice(0,12);
  box.innerHTML=list.map(card).join('')||`<div class="empty">Hozircha bo'sh</div>`;
  bindCards();
}
async function refresh(first){
  const grid=$('#grid');if(!grid)return;
  try{
    const q=(($('#q')||{}).value||'').trim(),sort=($('#sort')||{value:'popular'}).value;
    let url=`/api/products?q=${encodeURIComponent(q)}&category=${curCat}&sort=${sort}`;
    if(document.body.dataset.sale==='1')url+=`&sort=discount`;
    const r=await fetch(url);if(!r.ok)throw new Error('api');
    ALL=await r.json();
    if(document.body.dataset.sale==='1')ALL=ALL.filter(p=>p.discount_pct>0);
    grid.innerHTML=ALL.map(card).join('')||`<div class="empty">Hech narsa topilmadi</div>`;
    const cnt=$('#count');if(cnt)cnt.textContent=q?`"${q}" — ${ALL.length} ta topildi`:ALL.length+' ta topildi';
    if(first){renderCircles();paintHero();renderTabs()}
    bindCards();paintWish();
  }catch(e){const cnt=$('#count');if(cnt)cnt.textContent='';toast("Qidiruvda xatolik — sahifani yangilab ko'ring")}
}
function bindCards(){
  document.querySelectorAll('[data-add]').forEach(b=>b.onclick=e=>{e.stopPropagation();if(!b.disabled)add(b.dataset.add)});
  document.querySelectorAll('[data-link]').forEach(el=>{el.onclick=e=>{if(e.target.closest('[data-wish]')||e.target.closest('[data-add]'))return;location.href=el.dataset.link}});
  document.querySelectorAll('[data-wish]').forEach(b=>b.onclick=e=>{e.stopPropagation();toggleWish(b.dataset.wish)});
}
function toggleWish(slug){
  if(wish.has(slug)){wish.delete(slug);toast('Sevimlilardan olindi')}
  else{wish.add(slug);toast('Sevimlilarga qo‘shildi ♥')}
  localStorage.setItem('aza_wish',JSON.stringify([...wish]));
  document.querySelectorAll(`[data-wish="${slug}"]`).forEach(b=>{b.classList.toggle('on',wish.has(slug));b.textContent=wish.has(slug)?'♥':'♡'});
  paintWish();
  if($('#wishGrid'))renderWishPage();
}
function paintWish(){const n=wish.size,el=$('#wishN');if(!el)return;el.style.display=n?'grid':'none';el.textContent=n}
function findP(slug){return ALL.find(x=>x.slug===slug)||window._cur}
function add(slug,n=1){
  const p=findP(slug);
  if(!p)return;cart[slug]=Math.min(p.stock,(cart[slug]||0)+n);
  localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart();toast('Savatga qo‘shildi');
}
function cartItems(){return Object.entries(cart).map(([slug,qty])=>{const p=ALL.find(x=>x.slug===slug);return p?{...p,qty}:null}).filter(Boolean)}
function renderCart(){
  const cn=$('#cartN');const items=cartItems(),n=items.reduce((a,i)=>a+i.qty,0);
  if(cn)cn.textContent=n;
  const body=$('#cartBody'),foot=$('#cartFoot');if(!body||!foot)return;
  if(!items.length){body.innerHTML=`<div class="empty">Savat bo'sh<br><a href="/shop" class="btn btn-acc" style="margin-top:12px;display:inline-block" onclick="closeDrawer()">Gul tanlash</a></div>`;foot.innerHTML='';return}
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  body.innerHTML=items.map(i=>`<div class="citem">${flowerSVG(i,120,120)}<div><b style="font-size:13px">${i.name}</b><div style="color:var(--muted);font-size:13px">${fmt(i.price)}</div><div class="qty"><button onclick="chQty('${i.slug}',-1)">−</button><b>${i.qty}</b><button onclick="chQty('${i.slug}',1)">+</button></div></div><button class="pill" onclick="rm('${i.slug}')">✕</button></div>`).join('')
    +`<div style="border:1px dashed var(--accent-dark);padding:10px 12px;font-size:13px;color:var(--muted)">✦ ${CFG.delivery_note||"Yetkazish Yandex'ga alohida to'lanadi"}</div>`;
  foot.innerHTML=`<div class="row"><span>Gullar summasi:</span><b>${fmt(sub)}</b></div><div class="row"><span>Yetkazish:</span><b>Yandex alohida</b></div><div class="row ttl"><span>Jami:</span><span>${fmt(sub)}</span></div><button class="btn btn-acc" style="width:100%;margin-top:8px" onclick="location.href='/checkout'">Buyurtma berish →</button>`;
}
window.chQty=(s,d)=>{const p=ALL.find(x=>x.slug===s);cart[s]=(cart[s]||0)+d;if(cart[s]<=0)delete cart[s];if(p&&cart[s]>p.stock)cart[s]=p.stock;localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
window.rm=s=>{delete cart[s];localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
function openModal(s){const m=$(s);if(!m)return;m.classList.add('show');const o=$('#overlay');if(o)o.classList.add('show')}
function closeModal(s){const m=$(s);if(m)m.classList.remove('show');const d=$('#drawer');if(!d||!d.classList.contains('show')){const o=$('#overlay');if(o)o.classList.remove('show')}}
window.closeModal=closeModal;
function openDrawer(){const d=$('#drawer');if(!d)return;d.classList.add('show');const o=$('#overlay');if(o)o.classList.add('show');renderCart()}
function closeDrawer(){const d=$('#drawer');if(d)d.classList.remove('show');if(!document.querySelector('.modal.show')){const o=$('#overlay');if(o)o.classList.remove('show')}}
window.closeDrawer=closeDrawer;

/* ---------- mahsulot sahifasi ---------- */
async function initProductPage(){
  const box=$('#pDetail');if(!box)return;
  const slug=box.dataset.slug||decodeURIComponent((location.pathname.split('/product/')[1]||'').split('/')[0]);
  if(!slug){box.innerHTML='<div class="empty">Mahsulot topilmadi</div>';return}
  try{
    const p=await (await fetch('/api/products/'+slug)).json();
    if(p.detail){box.innerHTML='<div class="empty">Mahsulot topilmadi<br><a class="btn btn-acc" style="margin-top:12px;display:inline-block" href="/shop">Katalogga qaytish</a></div>';return}
    window._cur=p;
    const cat=(CATS.find(c=>c.slug===p.category)||{}).name||'';
    document.title=p.name+' — FAX Flores';
    box.innerHTML=`<div class="mgrid" style="border:1px solid var(--line)"><div class="l">${flowerSVG(p,600,600)}${badges(p)}</div>
    <div class="r"><div class="cat">${cat}</div><h2 style="font-family:var(--serif);font-size:34px;font-weight:400;margin:6px 0">${p.name}</h2>
    <div class="stars">★★★★★ <span>4.9 (120+)</span></div>
    <p style="color:var(--body);line-height:1.7;margin:12px 0">${p.description||''}</p>
    <div class="prow"><span class="price" style="font-size:26px">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div>
    <div class="form"><div class="qty"><button id="pqDec">−</button><b id="pq">1</b><button id="pqInc">+</button><span style="color:var(--muted);font-size:13px">Omborda: ${p.stock}</span></div>
    <button class="btn btn-acc" id="pAdd" style="width:100%" ${p.stock<=0?'disabled':''}>Savatga qo'shish</button>
    <button class="btn btn-outline" id="pWish" style="width:100%">♡ Sevimlilarga</button></div></div></div>
    ${p.related&&p.related.length?`<h3 style="font-family:var(--serif);font-size:26px;font-weight:400;margin:30px 0 16px">Tavsiya etamiz</h3><div class="grid">${p.related.map(card).join('')}</div>`:''}`;
    on('#pqDec','click',()=>{const e=$('#pq');e.textContent=Math.max(1,+e.textContent-1)});
    on('#pqInc','click',()=>{const e=$('#pq');e.textContent=Math.min(20,+e.textContent+1)});
    on('#pAdd','click',()=>{add(p.slug,+($('#pq').textContent))});
    on('#pWish','click',()=>toggleWish(p.slug));
    const bc=$('#crumbs');if(bc)bc.innerHTML=`<a href="/">Bosh sahifa</a> / <a href="/shop">Katalog</a> / <a href="/shop?cat=${p.category}">${cat}</a> / ${p.name}`;
    bindCards();paintWish();
  }catch(e){box.innerHTML='<div class="empty">Xatolik — qayta urining</div>'}
}

/* ---------- sevimlilar sahifasi ---------- */
function renderWishPage(){
  const box=$('#wishGrid');if(!box)return;
  const list=ALL.filter(p=>wish.has(p.slug));
  const cnt=$('#wishCount');if(cnt)cnt.textContent=list.length?list.length+' ta mahsulot':'Bo‘sh';
  box.innerHTML=list.map(card).join('')||`<div class="empty">Sevimlilar bo‘sh — mahsulotlarda ♡ bosing<br><a class="btn btn-acc" style="margin-top:12px;display:inline-block" href="/shop">Katalogga o‘tish</a></div>`;
  bindCards();
}

/* ---------- checkout ---------- */
const CO={ship:'standard',pay:'cash',promo:{code:'',pct:0},loc:null};
function coProfile(){
  let p={}; try{p=JSON.parse(localStorage.getItem('aza_profile')||'{}')}catch(e){p={}}
  if(!ME&&localStorage.getItem('aza_token')){try{ME=JSON.parse(localStorage.getItem('aza_user')||'null')}catch(e){ME=null}}
  if(ME){if(ME.name)p.name=ME.name; if(ME.phone)p.phone='+'+ME.phone}
  return p;
}
function saveProfile(f){try{localStorage.setItem('aza_profile',JSON.stringify(f))}catch(e){}}
function maskPhone(inp){
  if(!inp||inp._masked)return; inp._masked=true;
  inp.addEventListener('input',()=>{
    let d=inp.value.replace(/\D/g,'');
    if(d.startsWith('998'))d=d.slice(3);
    d=d.slice(0,9);
    let out='+998';
    if(d.length>0)out+=' '+d.slice(0,2);
    if(d.length>2)out+=' '+d.slice(2,5);
    if(d.length>5)out+=' '+d.slice(5,7);
    if(d.length>7)out+=' '+d.slice(7,9);
    inp.value=d.length?out:'';
  });
}
function shipFee(){const s=(CFG.ship||[]).find(x=>x.slug===CO.ship);return s?s.fee:(CO.ship==='express'?30000:0)}
function coTotals(){
  const items=cartItems();
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  const disc=Math.round(sub*CO.promo.pct/100);
  const ship=shipFee();
  const total=sub-disc+ship;
  const prepay=Math.round(total*(CFG.prepay_pct||50)/100);
  return {items,sub,disc,ship,total,prepay,rest:total-prepay};
}
function renderCheckout(){
  const box=$('#coBody');if(!box)return;
  if(!cartItems().length){box.innerHTML=`<div class="empty">Savat bo'sh<br><a class="btn btn-acc" style="margin-top:12px;display:inline-block" href="/shop">Gul tanlash</a></div>`;return}
  CO.ship='standard';CO.pay='cash';CO.promo={code:'',pct:0};
  const regions=CFG.regions||['Toshkent shahri'];
  const pr=coProfile();
  const ships=CFG.ship||[{slug:'standard',name:'Standart',hint:"Yandex orqali 3 soatgacha"},{slug:'express',name:'Tezkor',hint:'1 soatda · +30 000'}];
  box.innerHTML=`
  <h1 style="font-family:var(--serif);font-size:36px;font-weight:400;margin:0">Buyurtma berish</h1>
  <div id="coSummary" style="margin:14px 0"></div>
  <div class="cform" style="margin-top:6px">
  <div><h3>Promokod (% li chegirma)</h3>
    <div class="promo-row" style="margin-top:10px"><input id="promoInput" placeholder="Promokod" autocomplete="off"><button type="button" class="btn btn-outline" id="promoBtn" style="padding:12px 22px">Qo'llash</button></div>
    <p class="promo-msg" id="promoMsg"></p>
  </div>
  <p id="prepayCardLine" style="font-size:14px;color:var(--body)"></p>
  <form id="orderForm" novalidate>
    <div><h3>Aloqa ma'lumotlari</h3><div class="fgrid2" style="margin-top:10px">
      <label class="fld"><span>Ism Familiya *</span><input id="fName" name="name" autocomplete="name" placeholder="Ali Valiyev" value="${escA(pr.name)}"></label>
      <label class="fld"><span>Telefon *</span><input id="fPhone" name="phone" autocomplete="tel" inputmode="tel" placeholder="+998 90 770 81 24" value="${escA(pr.phone)}"></label>
    </div></div>
    <div><h3>Yetkazib berish manzili</h3><div class="fgrid2" style="margin-top:10px">
      <label class="fld"><span>Viloyat / shahar *</span><select id="fRegion" name="region" autocomplete="address-level1">${regions.map(r=>`<option ${pr.region===r?'selected':''}>${r}</option>`).join('')}</select></label>
      <label class="fld"><span>Tuman / shahar *</span><input id="fCity" name="city" autocomplete="address-level2" placeholder="Masalan: Chilonzor" value="${escA(pr.city)}"></label>
    </div>
      <label class="fld" style="margin-top:10px"><span>Manzil (ko'cha, uy) <small style="color:var(--muted)">— xarita belgilasangiz shart emas</small></span><input id="fAddr" name="address" autocomplete="street-address" placeholder="Masalan: Bunyodkor shoh ko'chasi 12" value="${escA(pr.address)}"></label>
      <div class="fld" style="margin-top:10px"><span>Xaritadan belgilash 📍</span><div class="mapwrap"><div id="orderMap" class="omap"></div><div class="mapbar"><button type="button" id="findMe" class="btn btn-outline btn--sm">📍 Meni topish</button><span class="mapcoords" id="mapCoords"></span></div></div></div>
      <label class="fld" style="margin-top:10px"><span>Izoh (kuryer uchun)</span><input id="fNote" name="note" autocomplete="off" placeholder="Masalan: 2-qavat, tabriknoma matni" value="${escA(pr.note)}"></label>
    </div>
    <div><h3>Yetkazish usuli</h3><div style="display:grid;gap:8px;margin-top:10px" id="coShip">
      ${ships.map(s=>`<label class="radio-card"><input type="radio" name="ship" value="${s.slug}" ${CO.ship===s.slug?'checked':''}><span><b>${s.name}</b><small>${s.hint||''}</small></span></label>`).join('')}
    </div></div>
    <div><h3>To'lov usuli</h3><div class="radio-cards" style="margin-top:10px" id="coPay">
      <label class="radio-card"><input type="radio" name="pay" value="cash" checked><span><b>Naqd / yetkazib berishda</b><small>Kuryerga naqd to'lov</small></span></label>
      <label class="radio-card"><input type="radio" name="pay" value="card"><span><b>Plastik karta</b><small>Yetkazib berishda terminal</small></span></label>
      <label class="radio-card"><input type="radio" name="pay" value="online"><span><b>Online to'lov</b><small>Payme / Click</small></span></label>
    </div></div>
    <button class="btn btn-acc" id="orderSubmit" style="width:100%;margin-top:6px">Tasdiqlash</button>
    <p class="hint">🔒 Ma'lumotlaringiz xavfsiz saqlanadi</p>
  </form></div>`;
  document.querySelectorAll('#coShip input').forEach(r=>r.onchange=()=>{CO.ship=r.value;refreshCo()});
  document.querySelectorAll('#coPay input').forEach(r=>r.onchange=()=>{CO.pay=r.value});
  on('#promoBtn','click',applyPromo);
  on('#orderForm','submit',e=>{e.preventDefault();submitOrderForm()});
  maskPhone($('#fPhone'));
  refreshCo();
  setTimeout(initCoMap,150);
}
function refreshCo(){
  const t=coTotals();
  const pct=CFG.prepay_pct||50;
  const card=(CFG.pay_card||'').replace(/\D/g,'').replace(/(\d{4})(?=\d)/g,'$1 ');
  const cl=$('#prepayCardLine');
  if(cl)cl.innerHTML=CFG.pay_card
    ? `💳 Oldindan to'lov (Click / Payme):<br><code id="payCardNum" style="background:#fff;border:1px dashed var(--accent-dark);padding:6px 12px;font-size:16px;letter-spacing:1px;cursor:pointer">${card}</code>`
    : `💳 50% oldindan to'lov: operatorimiz sizga karta yuboradi.`;
  on('#payCardNum','click',()=>{try{navigator.clipboard.writeText(CFG.pay_card);toast('Karta nusxalandi')}catch(e){}});
  const box2=$('#coSummary');
  if(box2)box2.innerHTML=t.items.map(i=>`<div class="sumrow"><span>${i.name} × ${i.qty}</span><b>${fmt(i.price*i.qty)}</b></div>`).join('')
    +(t.disc?`<div class="sumrow"><span>Promokod ${CO.promo.code} (−${CO.promo.pct}%)</span><b>−${fmt(t.disc)}</b></div>`:'')
    +`<div class="sumrow"><span>Yetkazish</span><b>${t.ship?fmt(t.ship):'Bepul'}</b></div>`
    +`<div class="sumrow total"><span>Jami</span><b>${fmt(t.total)}</b></div>`
    +`<div class="sumrow pre"><span>Oldindan to'lov · ${pct}%</span><b>${fmt(t.prepay)}</b></div>`
    +`<div class="sumrow"><span>Qolgan (yetkazishda)</span><b>${fmt(t.rest)}</b></div>`;
  const btn=$('#orderSubmit');
  if(btn)btn.textContent=`Tasdiqlash · ${fmt(t.total)} (oldindan ${fmt(t.prepay)})`;
}
async function applyPromo(){
  const inp=$('#promoInput'),msg=$('#promoMsg');if(!inp||!msg)return;
  const code=(inp.value||'').trim().toUpperCase();
  if(!code){CO.promo={code:'',pct:0};msg.textContent='';msg.className='promo-msg';refreshCo();return}
  msg.textContent='Tekshirilmoqda...';msg.className='promo-msg';
  try{
    const r=await fetch('/api/promo?code='+encodeURIComponent(code));
    if(r.status===404){msg.textContent='⛔ Promokod hozircha ishlamaydi';msg.className='promo-msg err';return}
    const j=await r.json();
    if(j.ok){CO.promo={code:j.code,pct:j.pct};msg.textContent=`✅ ${j.pct}% chegirma qo'llandi!`;msg.className='promo-msg ok'}
    else{CO.promo={code:'',pct:0};msg.textContent='⛔ '+(j.error||'topilmadi');msg.className='promo-msg err'}
  }catch(e){msg.textContent='⛔ Tekshirib bo‘lmadi';msg.className='promo-msg err'}
  refreshCo();
}
let pendingOrder=null;
function submitOrderForm(){
  const q=id=>{const el=document.getElementById(id);return el?el.value.trim():''};
  const body={name:q('fName'),phone:q('fPhone'),
    region:q('fRegion'),city:q('fCity'),address:q('fAddr'),
    note:q('fNote'),ship:CO.ship,pay:CO.pay,promo:CO.promo.code,
    items:cartItems().map(i=>({slug:i.slug,qty:i.qty}))};
  if(!body.name||!body.phone||!body.city)return toast('Iltimos, majburiy maydonlarni to‘ldiring');
  if(body.phone.replace(/\D/g,'').length<9){toast('Telefon raqamni to‘g‘ri kiriting');const p=$('#fPhone');if(p)p.focus();return}
  if(!body.address&&!CO.loc){toast('Manzilni yozing yoki xaritadan belgilang 📍');const a=$('#fAddr');if(a)a.focus();return}
  if(!body.items.length)return toast('Savat bo‘sh');
  saveProfile({name:body.name,phone:body.phone,region:body.region,city:body.city,address:body.address,note:body.note});
  body.lat=CO.loc?CO.loc.lat:null; body.lon=CO.loc?CO.loc.lon:null;
  pendingOrder=body;
  openModal('#polmodal');
}
async function doSubmit(){
  const body=pendingOrder;pendingOrder=null;
  if(!body)return;
  closeModal('#polmodal');
  const btn=$('#orderSubmit');
  const btnTxt=btn?btn.textContent:'';
  if(btn){btn.disabled=true;btn.textContent='Yuborilmoqda...'}
  try{
    const r=await fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(body)});
    const o=await r.json();
    if(btn){btn.disabled=false;btn.textContent=btnTxt}
    if(!r.ok){toast('Yuborilmadi: '+(o.detail||'qayta urining'));return}
    cart={};localStorage.setItem('aza_cart','{}');renderCart();
    showSuccess(o,body);
  }catch(e){if(btn){btn.disabled=false;btn.textContent=btnTxt}toast('Xatolik — internetni tekshiring')}
}
function showSuccess(o,form){
  const box=$('#coBody');if(!box)return;
  const no=o.no||('FAX-'+(o.id||o.order_id));
  const botUrl=o.bot_url||`https://t.me/${BOT_USERNAME}?start=ord_${o.id||o.order_id}`;
  box.innerHTML=`<div style="text-align:center;padding:10px 0;max-width:560px;margin:0 auto">
    <div style="font-size:52px">✓</div>
    <h2 style="font-family:var(--serif);font-weight:400;font-size:30px;margin:8px 0">Buyurtma ${no} qabul qilindi!</h2>
    <p style="color:var(--body)">Rahmat, <b>${escA(form.name)}</b>!</p>
    <div style="text-align:left;border:1px solid var(--line);padding:16px;margin:16px 0">
      <div class="sumrow"><span>Jami</span><b>${fmt(o.total)}</b></div>
      <div class="sumrow pre"><span>Oldindan 50%</span><b>${fmt(o.prepay)}</b></div>
      <div class="sumrow"><span>Qolgan</span><b>${fmt(o.total-o.prepay)}</b></div>
    </div>
    <div class="obotgo">
      <h3 style="font-family:var(--serif);font-weight:400;font-size:22px;margin:6px 0">Keyingi qadam — 50% to'lov 💳</h3>
      <p style="color:var(--body);font-size:14px"><b>${fmt(o.prepay)}</b> ni to'lang va chekni botga yuboring.</p>
      <a class="btn btn-acc" style="width:100%;margin-top:8px" target="_blank" rel="noopener" href="${botUrl}">✈ Botga o'tish va chek yuborish</a>
      <p class="hint">⚠️ Aynan <b>${fmt(o.prepay)}</b> to'lang — ko'p ham, kam ham emas. Chek tekshirilgach, buyurtma adminga o'tadi.</p>
    </div>
  </div>`;
  window.scrollTo({top:0,behavior:'smooth'});
  pollOrder(o.id||o.order_id,0);
}
async function pollOrder(oid,n){
  const box=document.querySelector('#coBody .obotgo, #coBody .ocheck');
  if(!box)return;
  if(n>144)return;
  try{
    const r=await fetch('/api/order?id='+oid);
    const j=await r.json();
    if(j&&j.ok){
      const st=j.status;
      if(st==='awaiting_confirm'&&!box.classList.contains('ocheck')){
        box.outerHTML=`<div class="obotgo ocheck" style="text-align:center"><h3 style="font-family:var(--serif);font-weight:400;font-size:22px">📸 Chek qabul qilindi!</h3><p style="color:var(--body);font-size:14px">Admin tekshirmoqda, kuting...</p></div>`;
      }else if(['accepted','qabul','preparing','delivering','delivered','closed'].includes(st)){
        const el=document.querySelector('#coBody .obotgo, #coBody .ocheck');
        if(el)el.outerHTML=`<div class="obotgo" style="text-align:center"><div style="font-size:52px">✓</div><h3 style="font-family:var(--serif);font-weight:400;font-size:22px">Buyurtma qabul qilindi, rahmat! 🎉</h3><p style="color:var(--body);font-size:14px">To'lovingiz tasdiqlandi. Tez orada bog'lanamiz.</p></div>`;
        return;
      }else if(['rejected','cancelled'].includes(st)){
        const el=document.querySelector('#coBody .obotgo, #coBody .ocheck');
        if(el)el.outerHTML=`<div class="obotgo" style="text-align:center"><h3 style="font-family:var(--serif);font-weight:400;font-size:22px">❌ Buyurtma tasdiqlanmadi</h3><p style="color:var(--body);font-size:14px">Chekda muammo topildi. Operatorimiz siz bilan bog'lanadi.</p></div>`;
        return;
      }
    }
  }catch(e){}
  setTimeout(()=>pollOrder(oid,n+1),5000);
}
/* xarita */
let coMap=null,coMarker=null;
function initCoMap(){
  const el=document.getElementById('orderMap');
  if(!el||typeof L==='undefined')return;
  if(coMap){try{coMap.remove()}catch(e){} coMap=null;coMarker=null}
  CO.loc=null;
  coMap=L.map('orderMap').setView([41.3111,69.2797],12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(coMap);
  coMap.on('click',e=>placeCoLoc(e.latlng.lat,e.latlng.lng));
  setTimeout(()=>coMap&&coMap.invalidateSize(),300);
  on('#findMe','click',()=>{
    if(!navigator.geolocation)return toast('Geolokatsiya topilmadi');
    toast('Joylashuv aniqlanmoqda...');
    navigator.geolocation.getCurrentPosition(p=>{
      placeCoLoc(p.coords.latitude,p.coords.longitude);
      coMap.setView([p.coords.latitude,p.coords.longitude],15);
    },()=>toast('Ruxsat berilmadi — xaritani bosing 📍'),{timeout:10000});
  });
}
function placeCoLoc(lat,lon){
  CO.loc={lat:+lat.toFixed(6),lon:+lon.toFixed(6)};
  if(typeof L!=='undefined'){
    if(coMarker)coMarker.setLatLng([lat,lon]);
    else if(coMap)coMarker=L.marker([lat,lon]).addTo(coMap);
  }
  const mc=document.getElementById('mapCoords');
  if(mc)mc.textContent=`📍 ${CO.loc.lat}, ${CO.loc.lon}`;
  revGeo(lat,lon);
}
const ISO_REG={'UZ-TK':'Toshkent shahri','UZ-TO':'Toshkent viloyati','UZ-SA':'Samarqand','UZ-BU':'Buxoro','UZ-AN':'Andijon','UZ-FA':"Farg'ona",'UZ-NG':'Namangan','UZ-QA':'Qashqadaryo','UZ-SU':'Surxondaryo','UZ-XO':'Xorazm','UZ-NW':'Navoiy','UZ-JI':'Jizzax','UZ-SI':'Sirdaryo','UZ-QR':"Qoraqalpog'iston"};
let revTimer=null,revSeq=0;
function normW(x){return String(x||'').toLowerCase().replace(/['ʼ`]/g,'')}
function matchRegion(s){
  const n=normW(s).replace(/[^a-z ]/g,'');
  for(const o of (CFG.regions||[])){
    const w=normW(o).split(' ')[0].replace(/[^a-z]/g,'');
    if(w&&w.length>2&&n.includes(w))return o;
  }
  return '';
}
function revGeo(lat,lon){
  clearTimeout(revTimer);
  const my=++revSeq;
  revTimer=setTimeout(async()=>{
    const mc=document.getElementById('mapCoords');
    if(mc)mc.textContent='📍 Manzil qidirilmoqda...';
    try{
      const r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&accept-language=uz,ru`);
      const j=await r.json();
      if(my!==revSeq)return;
      const a=j.address||{};
      const addr=[a.road||'',a.house_number||''].filter(Boolean).join(', ')||a.suburb||a.neighbourhood||a.quarter||a.district||a.city||a.town||a.village||'';
      const fa=document.getElementById('fAddr');
      if(fa&&addr)fa.value=addr;
      const dist=a.suburb||a.city_district||a.district||a.neighbourhood||a.quarter||a.town||a.village||'';
      const fc=document.getElementById('fCity');
      if(fc&&dist)fc.value=dist;
      const reg=ISO_REG[a['ISO3166-2-lvl4']]||matchRegion(a.state||a.county||a.city||'');
      if(reg){const fr=document.getElementById('fRegion');if(fr)fr.value=reg}
      if(mc)mc.textContent=`📍 ${addr||(lat+', '+lon)}`;
      if(addr)toast('📍 Manzil avtomatik to‘ldirildi');
    }catch(e){if(mc&&my===revSeq)mc.textContent=`📍 ${lat}, ${lon}`}
  },450);
}
/* aksiya taymeri — yakshanba 23:59 gacha */
function initCd(){
  if(!document.getElementById('cd-d'))return;
  const tick=()=>{
    const now=new Date();const end=new Date(now);
    end.setDate(now.getDate()+((7-now.getDay())%7));
    end.setHours(23,59,59,0);
    if(end<now)end.setDate(end.getDate()+7);
    let s=Math.max(0,Math.floor((end-now)/1000));
    const d=Math.floor(s/86400);s%=86400;
    const h=Math.floor(s/3600),m=Math.floor(s%3600/60),ss=s%60;
    const set=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
    set('cd-d',d);set('cd-h',String(h).padStart(2,'0'));set('cd-m',String(m).padStart(2,'0'));set('cd-s',String(ss).padStart(2,'0'));
  };
  tick();setInterval(tick,1000);
}
let curSlide=0,slideTimer=null;
function showSlide(i){
  const slides=document.querySelectorAll('.slide');if(!slides.length)return;
  curSlide=(i+slides.length)%slides.length;
  slides.forEach((s,k)=>s.classList.toggle('on',k===curSlide));
  document.querySelectorAll('#slideDots button').forEach((d,k)=>d.classList.toggle('on',k===curSlide));
}
function initSlider(){
  const slides=document.querySelectorAll('.slide');if(!slides.length)return;
  const dots=$('#slideDots');
  if(dots&&!dots.innerHTML)dots.innerHTML=[...slides].map((_,k)=>`<button data-dot="${k}" class="${k===0?'on':''}"></button>`).join('');
  if(dots)dots.onclick=e=>{const b=e.target.closest('[data-dot]');if(b){showSlide(+b.dataset.dot);restartAuto()}};
  on('#slidePrev','click',()=>{showSlide(curSlide-1);restartAuto()});
  on('#slideNext','click',()=>{showSlide(curSlide+1);restartAuto()});
  restartAuto();
}
function restartAuto(){clearInterval(slideTimer);slideTimer=setInterval(()=>showSlide(curSlide+1),5000)}
/* global bindings */
function bindChrome(){
  on('#openCart','click',openDrawer);
  on('#closeCart','click',closeDrawer);
  on('#overlay','click',()=>{closeDrawer();document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'));const mm=$('#mmenu');if(mm)mm.classList.remove('show')});
  document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'));const d=$('#drawer');if(!d||!d.classList.contains('show')){const o=$('#overlay');if(o)o.classList.remove('show')}});
  on('#burger','click',()=>{const m=$('#mmenu');if(m)m.classList.add('show');const o=$('#overlay');if(o)o.classList.add('show')});
  on('#mmenuX','click',()=>{const m=$('#mmenu');if(m)m.classList.remove('show');const o=$('#overlay');if(o)o.classList.remove('show')});
  document.querySelectorAll('#mmenu [data-navcat]').forEach(a=>a.onclick=()=>{location.href='/shop?cat='+a.dataset.navcat});
  on('#searchBtn','click',()=>{const s=$('#searchOv');if(s)s.classList.add('show');setTimeout(()=>{const q=$('#q');if(q)q.focus()},50)});
  on('#searchX','click',()=>{const s=$('#searchOv');if(s)s.classList.remove('show')});
  on('#pills','click',e=>{if(e.target.dataset&&e.target.dataset.cat){curCat=e.target.dataset.cat;renderPills();refresh()}});
  document.querySelectorAll('.tabbtn').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabbtn').forEach(x=>x.classList.remove('on'));b.classList.add('on');curTab=b.dataset.tab;renderTabs()});
  document.querySelectorAll('[data-navcat]').forEach(a=>{if(a.closest('#mmenu'))return;a.onclick=e=>{e.preventDefault();location.href='/shop?cat='+a.dataset.navcat}});
  on('#sort','change',()=>refresh());
  on('#q','input',()=>{clearTimeout(window._qt);window._qt=setTimeout(()=>{if($('#grid'))refresh();else{const v=$('#q').value;location.href='/shop?q='+encodeURIComponent(v)}},600)});
  on('#q','keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(window._qt);if($('#grid')){refresh();const s=$('#searchOv');if(s)s.classList.remove('show');const k=document.getElementById('katalog');if(k)k.scrollIntoView()}else{location.href='/shop?q='+encodeURIComponent($('#q').value)}}});
  on('#wishBtn','click',()=>{location.href='/wishlist'});
  on('#fWish','click',e=>{e.preventDefault();location.href='/wishlist'});
  on('#fCart','click',e=>{e.preventDefault();openDrawer()});
  on('#tabLogin','click',()=>switchTab('login'));
  on('#tabReg','click',()=>switchTab('reg'));
  on('#doLogin','click',()=>{const ph=$('#lPhone').value.trim(),pw=$('#lPass').value;if(ph.length<7||!pw)return toast('Telefon va parolni kiriting');doAuth('/api/auth/login',{phone:ph,password:pw})});
  on('#doReg','click',()=>{const nm=$('#rName').value.trim(),ph=$('#rPhone').value.trim(),pw=$('#rPass').value;if(nm.length<2||ph.length<7||pw.length<4)return toast("Ma'lumotlarni to'liq kiriting");doAuth('/api/auth/register',{name:nm,phone:ph,password:pw})});
  document.addEventListener('click',e=>{if(e.target.closest('[data-polclose]')){pendingOrder=null;closeModal('#polmodal')}});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){pendingOrder=null;closeModal('#polmodal')}});
  document.addEventListener('click',e=>{if(e.target&&e.target.id==='policyOk')doSubmit()});
  const cf=$('#contactForm');
  if(cf)cf.onsubmit=e=>{e.preventDefault();
    const n=$('#cName').value.trim(),p=$('#cPhone').value.trim(),m=$('#cMsg').value.trim();
    if(n.length<2||p.length<7||m.length<3)return toast("Barchasini to'ldiring");
    const u=(CFG.contact&&CFG.contact.telegram)||'https://t.me/azaflowers';
    try{navigator.clipboard.writeText(`💬 FAX xabar\n👤 ${n}\n📞 ${p}\n\n${m}`).catch(()=>{})}catch(e){}
    window.open(u,'_blank');toast('Xabar nusxalandi — Telegramda yuboring');
  };
  if(location.hash==='#kirish')openModal('#amodal');
}
document.addEventListener('DOMContentLoaded',()=>{
  bindChrome();
  initCd();
  renderCart();paintWish();
  load().then(async()=>{await loadMe();paintAuth();renderCart();paintWish()}).catch(()=>toast("Ma'lumot yuklanmadi — internetni tekshiring"));
});
window.add=add;window.view=null;window.toggleWish=toggleWish;
