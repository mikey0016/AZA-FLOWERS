const $=s=>document.querySelector(s);
let ALL=[],CATS=[],CFG={delivery_fee:0,free_delivery_from:null,delivery_note:'',contact:{}},curCat='all',curTab='new';
let cart=JSON.parse(localStorage.getItem('aza_cart')||'{}');
let wish=new Set(JSON.parse(localStorage.getItem('aza_wish')||'[]'));
const fmt=n=>n.toLocaleString('uz-UZ').replace(/,/g,' ')+" so'm";
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),2600)}
let ME=null;
function authHeaders(){const t=localStorage.getItem('aza_token');return t?{'Authorization':'Bearer '+t}:{}}
async function loadMe(){const t=localStorage.getItem('aza_token');if(!t)return null;try{const r=await fetch('/api/auth/me',{headers:authHeaders()});if(!r.ok){localStorage.removeItem('aza_token');localStorage.removeItem('aza_user');return null}ME=await r.json();localStorage.setItem('aza_user',JSON.stringify(ME));return ME}catch(e){return null}}
function paintAuth(){const el=$('#authArea');if(!el)return;if(ME){el.innerHTML=`<a class="linkbtn" href="/cabinet">${ME.name.split(' ')[0]} → Kabinet</a>`}else{el.innerHTML=`<button class="linkbtn" id="liBtn">Kirish</button>`;$('#liBtn').onclick=()=>openModal('#amodal')}}
function switchTab(w){document.getElementById('tabLogin').classList.toggle('on',w==='login');document.getElementById('tabReg').classList.toggle('on',w==='reg');document.getElementById('paneLogin').style.display=w==='login'?'grid':'none';document.getElementById('paneReg').style.display=w==='reg'?'grid':'none'}
async function doAuth(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){toast('Xatolik: '+(d.detail||'qayta urining'));return}localStorage.setItem('aza_token',d.token);localStorage.setItem('aza_user',JSON.stringify(d.user));ME=d.user;paintAuth();closeModal('#amodal');toast(`Xush kelibsiz, ${ME.name}!`)}

// Rasm: photo bo'lsa photo, bo'lmasa procedural SVG
function flowerSVG(p,w=400,h=340){
  if(p.photo)return `<div style="aspect-ratio:${w}/${h};overflow:hidden"><img src="${p.photo}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block"></div>`;
  const o=p.img||{petals:12,petal:'#e84393',center:'#f6c445',bg:['#fdf6ee','#fbe9ef'],leaves:true};
  const cx=w/2,cy=h/2-10,R=Math.min(w,h)*0.30;let s='';
  for(let i=0;i<o.petals;i++){const a=i/o.petals*Math.PI*2;
    const x=cx+Math.cos(a)*R*0.62,y=cy+Math.sin(a)*R*0.62;
    s+=`<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="${(R*0.42).toFixed(1)}" ry="${(R*0.24).toFixed(1)}" fill="${o.petal}" opacity=".95" transform="rotate(${(a*180/Math.PI).toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})"/>`}
  let lv=o.leaves?`<path d="M${cx-70} ${h-30} Q ${cx-30} ${h-90} ${cx-8} ${cy+40} Q ${cx-50} ${h-60} ${cx-70} ${h-30}Z" fill="#2f9e63"/><path d="M${cx+70} ${h-30} Q ${cx+30} ${h-90} ${cx+8} ${cy+40} Q ${cx+50} ${h-60} ${cx+70} ${h-30}Z" fill="#37b472"/>`:'';
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
  const w=wish.has(p.slug)?'on':'';
  return `<div class="card"><div class="imgw" data-view="${p.slug}">${flowerSVG(p)}${badges(p)}<button class="wish ${w}" data-wish="${p.slug}">${wish.has(p.slug)?'♥':'♡'}</button><span class="stock">${p.stock>0?'Mavjud':'Tugadi'}</span></div>
  <div class="pbody"><div class="cat">${cat}</div><div class="name" data-view="${p.slug}">${p.name}</div>
  <div class="prow"><span class="price">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div>
  <button class="add" data-add="${p.slug}" ${p.stock<=0?'disabled':''}>Savatga qo'shish</button></div></div>`;
}
async function load(){
  const [cfg,cats]=await Promise.all([(await fetch('/api/config')).json(),(await fetch('/api/categories')).json()]);
  CFG=cfg;CATS=cats;
  const total=cats.reduce((a,c)=>a+c.total,0);
  $('#cfgLine').textContent=`${total} mahsulot • Yandex orqali 3 soatgacha yetkazish`;
  $('#delText').textContent=(cfg.delivery_note||'')+' Har kuni 08:00–22:00.';
  const c=cfg.contact;
  if(c.phones&&c.phones[0])$('#hPhone').textContent=c.phones[0];
  const admins=(c.admins||[]).map(a=>`<a href="https://t.me/${a.replace('@','')}" target="_blank" style="color:var(--brand);font-weight:700">${a}</a>`).join(', ');
  const phones=(c.phones||[]).map(p=>`<a href="tel:${p.replace(/\s/g,'')}" style="color:var(--brand);font-weight:700">${p}</a>`).join(', ');
  $('#contactBox').innerHTML=`Telefonlar: ${phones}<br>Manzil: ${c.address}<br>Ish vaqti: ${c.hours}<br>Adminlar: ${admins}`;
  $('#footContact').innerHTML=(c.phones||[]).map(p=>`<div class="frow"><div><a href="tel:${p.replace(/\s/g,'')}">${p}</a></div></div>`).join('')+`<div class="frow"><div>${c.address}</div></div><div class="frow"><div>${c.hours}</div></div>`;
  $('#footCats').innerHTML=cats.map(x=>`<a href="#katalog" data-fcat="${x.slug}">${x.name}</a>`).join('');
  $('#footCats').onclick=e=>{const a=e.target.closest('[data-fcat]');if(!a)return;curCat=a.dataset.fcat;renderPills();refresh()};
  $('#tgBtn').href=c.telegram;$('#insBtn').href=c.instagram;
  $('#tgBtnF').href=c.telegram;$('#insBtnF').href=c.instagram;
  renderPills();renderCircles();await refresh(true);renderTabs();
}
function renderPills(){
  $('#pills').innerHTML=[{slug:'all',name:'Barchasi'},...CATS].map(c=>`<button class="pill ${curCat===c.slug?'on':''}" data-cat="${c.slug}">${c.name}</button>`).join('');
}
function renderCircles(){
  const box=$('#catCircles');if(!box)return;
  const counts={};ALL.forEach(p=>counts[p.category]=(counts[p.category]||0)+1);
  // ALL hali bo'sh bo'lishi mumkin — CATS dan olamiz
  box.innerHTML=CATS.map(c=>{
    const rep=ALL.find(p=>p.category===c.slug)||{slug:c.slug,img:{petals:12,petal:'#e88ca5',center:'#ffd166',bg:['#fdf6ee','#fbe9ef'],leaves:true}};
    return `<div class="catcircle" data-cat="${c.slug}"><div class="im"><div>${flowerSVG(rep,200,200)}</div></div><b>${c.name}</b><small>${c.total||''} mahsulot</small></div>`;
  }).join('');
  box.onclick=e=>{const el=e.target.closest('[data-cat]');if(!el)return;curCat=el.dataset.cat;renderPills();refresh();document.getElementById('katalog').scrollIntoView({behavior:'smooth'})};
}
function renderTabs(){
  let list=[...ALL];
  if(curTab==='new')list=list.filter(p=>p.is_featured===2||p.is_featured===1).slice(0,8);
  else if(curTab==='hit')list=list.filter(p=>p.is_featured===1).slice(0,8);
  else list=list.filter(p=>p.discount_pct>0).slice(0,8);
  if(!list.length)list=ALL.slice(0,8);
  $('#tabGrid').innerHTML=list.map(card).join('')||`<div class="empty">Hozircha bo'sh</div>`;
  bindCards();
}
async function refresh(first){
  try{
    const q=($('#q').value||'').trim(),sort=$('#sort').value;
    const url=`/api/products?q=${encodeURIComponent(q)}&category=${curCat}&sort=${sort}`;
    const r=await fetch(url);if(!r.ok)throw new Error('api');
    ALL=await r.json();
    $('#grid').innerHTML=ALL.map(card).join('')||`<div class="empty">Hech narsa topilmadi</div>`;
    $('#count').textContent=q?`"${q}" — ${ALL.length} ta topildi`:ALL.length+' ta topildi';
    if(first){
      renderCircles();
      const top=ALL.filter(p=>p.is_featured||p.discount_pct).slice(0,4);
      const hb=top.length?top:ALL.slice(0,4);
      $('#heroVis').innerHTML=hb.map(p=>`<div class="hcard">${flowerSVG(p,300,220)}<div class="t"><span>${p.name.slice(0,20)}…</span><b>${fmt(p.price)}</b></div></div>`).join('');
      renderTabs();
    }
    bindCards();paintWish();
  }catch(e){$('#count').textContent='';toast("Qidiruvda xatolik — sahifani yangilab ko'ring")}
}
function bindCards(){
  document.querySelectorAll('[data-add]').forEach(b=>b.onclick=e=>{e.stopPropagation();add(b.dataset.add)});
  document.querySelectorAll('[data-view]').forEach(el=>{el.onclick=e=>{if(e.target.closest('[data-wish]'))return;view(el.dataset.view)}});
  document.querySelectorAll('[data-wish]').forEach(b=>b.onclick=e=>{e.stopPropagation();toggleWish(b.dataset.wish)});
}
function toggleWish(slug){
  if(wish.has(slug)){wish.delete(slug);toast('Sevimlilardan olindi')}
  else{wish.add(slug);toast('Sevimlilarga qo‘shildi ♡')}
  localStorage.setItem('aza_wish',JSON.stringify([...wish]));
  document.querySelectorAll(`[data-wish="${slug}"]`).forEach(b=>{b.classList.toggle('on',wish.has(slug));b.textContent=wish.has(slug)?'♥':'♡'});
  paintWish();
}
function paintWish(){const n=wish.size,el=$('#wishN');if(!el)return;el.style.display=n?'grid':'none';el.textContent=n}
function add(slug,n=1){
  const p=ALL.find(x=>x.slug===slug)||window._cur;
  if(!p)return;cart[slug]=Math.min(p.stock,(cart[slug]||0)+n);
  localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart();toast('Savatga qo‘shildi');
}
function cartItems(){return Object.entries(cart).map(([slug,qty])=>{const p=ALL.find(x=>x.slug===slug);return p?{...p,qty}:null}).filter(Boolean)}
function renderCart(){
  const items=cartItems(),n=items.reduce((a,i)=>a+i.qty,0);$('#cartN').textContent=n;
  if(!items.length){$('#cartBody').innerHTML=`<div class="empty">Savat bo'sh<br><a href="#katalog" class="btn btn-dark" style="margin-top:12px;display:inline-block" onclick="closeDrawer()">Gul tanlash</a></div>`;$('#cartFoot').innerHTML='';return}
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  $('#cartBody').innerHTML=items.map(i=>`<div class="citem">${flowerSVG(i,120,120)}<div><b style="font-size:13px">${i.name}</b><div style="color:var(--muted);font-size:13px">${fmt(i.price)}</div><div class="qty"><button onclick="chQty('${i.slug}',-1)">−</button><b>${i.qty}</b><button onclick="chQty('${i.slug}',1)">+</button></div></div><button class="linkbtn" onclick="rm('${i.slug}')">✕</button></div>`).join('')
    +`<div style="border:1px dashed var(--gold);border-radius:12px;padding:10px 12px;font-size:13px;color:var(--muted);background:#fff">✦ ${CFG.delivery_note||"Yetkazish Yandex'ga alohida to'lanadi"}</div>`;
  $('#cartFoot').innerHTML=`<div class="row"><span>Gullar summasi:</span><b>${fmt(sub)}</b></div><div class="row"><span>Yetkazish:</span><b>Yandex alohida</b></div><div class="row ttl"><span>Jami:</span><span>${fmt(sub)}</span></div><button class="btn btn-dark" style="width:100%;margin-top:8px" onclick="openCheckout()">Buyurtma berish →</button>`;
}
window.chQty=(s,d)=>{const p=ALL.find(x=>x.slug===s);cart[s]=(cart[s]||0)+d;if(cart[s]<=0)delete cart[s];if(p&&cart[s]>p.stock)cart[s]=p.stock;localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
window.rm=s=>{delete cart[s];localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
async function view(slug){
  const p=await (await fetch('/api/products/'+slug)).json();window._cur=p;
  const cat=(CATS.find(c=>c.slug===p.category)||{}).name||'';
  $('#pmImg').innerHTML=flowerSVG(p,500,420)+badges(p);
  $('#pmBody').innerHTML=`<div class="cat">${cat}</div><h2>${p.name}</h2><p style="color:var(--muted);line-height:1.6">${p.description}</p><div class="prow"><span class="price" style="font-size:24px">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div><div class="form"><div class="qty"><button onclick="mQty(-1)">−</button><b id="mq">1</b><button onclick="mQty(1)">+</button><span style="color:var(--muted);font-size:13px">Omborda: ${p.stock}</span></div><button class="btn btn-dark" onclick="add('${p.slug}',+document.querySelector('#mq').textContent);closeModal('#pmodal')">Savatga qo'shish</button><button class="btn btn-light" onclick="toggleWish('${p.slug}')">♡ Sevimlilarga</button></div>${p.related?.length?`<h3 style="font-family:var(--serif);font-size:24px">Tavsiya etamiz:</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${p.related.map(r=>`<div style="border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer" onclick="view('${r.slug}')">${flowerSVG(r,200,140)}<div style="padding:8px;font-size:12px;font-weight:700">${r.name}<br>${fmt(r.price)}</div></div>`).join('')}</div>`:''}`;
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
window.openCheckout=()=>{const items=cartItems();if(!items.length)return;const sub=items.reduce((a,i)=>a+i.price*i.qty,0);if(ME){if(!$('#fName').value)$('#fName').value=ME.name;if(!$('#fPhone').value)$('#fPhone').value='+'+ME.phone}$('#sumLine').textContent=`${items.length} tur • Gullar: ${fmt(sub)}. Yetkazish Yandex'ga alohida to'lanadi.`;closeDrawer();openModal('#cmodal')};
$('#openCart').onclick=openDrawer;$('#closeCart').onclick=closeDrawer;$('#overlay').onclick=()=>{closeDrawer();document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'))};
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.modal.show').forEach(m=>m.classList.remove('show'));if(!$('#drawer').classList.contains('show'))$('#overlay').classList.remove('show')});
$('#pills').onclick=e=>{if(e.target.dataset.cat){curCat=e.target.dataset.cat;renderPills();refresh()}};
document.querySelectorAll('.tabbtn').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabbtn').forEach(x=>x.classList.remove('on'));b.classList.add('on');curTab=b.dataset.tab;renderTabs()});
document.querySelectorAll('[data-navcat]').forEach(a=>a.onclick=()=>{curCat=a.dataset.navcat;renderPills();refresh()});
$('#mainNav').onclick=e=>{const a=e.target.closest('[data-navcat]');if(a){curCat=a.dataset.navcat;renderPills();refresh()}};
$('#sort').onchange=()=>refresh();let qt;
const doSearch=()=>{clearTimeout(qt);refresh()};
$('#q').addEventListener('input',()=>{clearTimeout(qt);qt=setTimeout(refresh,300)});
$('#qBtn')?.addEventListener?.('click',doSearch);
$('#wishBtn').onclick=()=>{
  if(!wish.size)return toast('Sevimlilar bo‘sh — ♡ bosing');
  const list=ALL.filter(p=>wish.has(p.slug));
  $('#grid').innerHTML=list.map(card).join('');bindCards();
  document.getElementById('katalog').scrollIntoView({behavior:'smooth'});
  toast(`${list.length} ta sevimli ko'rsatildi`);
};
$('#sendOrder').onclick=async()=>{
  const body={name:$('#fName').value.trim(),phone:$('#fPhone').value.trim(),address:$('#fAddr').value.trim(),comment:$('#fCom').value.trim(),items:cartItems().map(i=>({slug:i.slug,qty:i.qty}))};
  if(body.name.length<2)return toast('Ismingizni yozing');if(body.phone.length<7)return toast('Telefonni yozing');if(body.address.length<5)return toast('Manzilni yozing');if(!body.items.length)return toast('Savat bo‘sh');
  const r=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(body)});
  if(!r.ok){const e=await r.json();return toast('Xatolik: '+e.detail)}const o=await r.json();
  cart={};localStorage.setItem('aza_cart','{}');renderCart();closeModal('#cmodal');
  toast(`Rahmat! Buyurtma #${o.order_id} qabul qilindi. Jami: ${fmt(o.total)}`);
};
load().then(async()=>{await loadMe();paintAuth();renderCart();paintWish()});
document.getElementById('tabLogin').onclick=()=>switchTab('login');
document.getElementById('tabReg').onclick=()=>switchTab('reg');
document.getElementById('doLogin').onclick=()=>{const ph=document.getElementById('lPhone').value.trim(),pw=document.getElementById('lPass').value;if(ph.length<7||!pw)return toast('Telefon va parolni kiriting');doAuth('/api/auth/login',{phone:ph,password:pw})};
document.getElementById('doReg').onclick=()=>{const nm=document.getElementById('rName').value.trim(),ph=document.getElementById('rPhone').value.trim(),pw=document.getElementById('rPass').value;if(nm.length<2||ph.length<7||pw.length<4)return toast("Ma'lumotlarni to'liq kiriting");doAuth('/api/auth/register',{name:nm,phone:ph,password:pw})};
if(location.hash==='#kirish')openModal('#amodal');
