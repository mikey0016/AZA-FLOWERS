const $=s=>document.querySelector(s);
let ALL=[],CATS=[],CFG={delivery_fee:0,free_delivery_from:null,delivery_note:'',contact:{}},curCat='all',curTab='new';
let cart={}; try{cart=JSON.parse(localStorage.getItem('aza_cart')||'{}')}catch(e){cart={}}
let wish=new Set(JSON.parse(localStorage.getItem('aza_wish')||'[]'));
const fmt=n=>(Number(n)||0).toLocaleString('uz-UZ').replace(/,/g,' ')+" so'm";
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),2600)}
let ME=null;
function authHeaders(){const t=localStorage.getItem('aza_token');return t?{'Authorization':'Bearer '+t}:{}}
async function loadMe(){const t=localStorage.getItem('aza_token');if(!t)return null;try{const r=await fetch('/api/auth/me',{headers:authHeaders()});if(!r.ok){localStorage.removeItem('aza_token');localStorage.removeItem('aza_user');return null}ME=await r.json();localStorage.setItem('aza_user',JSON.stringify(ME));return ME}catch(e){return null}}
function paintAuth(){const el=$('#authArea');if(!el)return;if(ME){el.innerHTML=`<a class="pill" href="/cabinet">${ME.name.split(' ')[0]} → Kabinet</a>`}else{el.innerHTML=`<button class="iconbtn" id="liBtn" title="Kirish" style="font-size:20px">👤</button>`;$('#liBtn').onclick=()=>openModal('#amodal')}}
function switchTab(w){document.getElementById('tabLogin').classList.toggle('on',w==='login');document.getElementById('tabReg').classList.toggle('on',w==='reg');document.getElementById('paneLogin').style.display=w==='login'?'grid':'none';document.getElementById('paneReg').style.display=w==='reg'?'grid':'none'}
async function doAuth(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){toast('Xatolik: '+(d.detail||'qayta urining'));return}localStorage.setItem('aza_token',d.token);localStorage.setItem('aza_user',JSON.stringify(d.user));ME=d.user;paintAuth();closeModal('#amodal');toast(`Xush kelibsiz, ${ME.name}!`)}

function flowerSVG(p,w=400,h=400){
  if(p.photo)return `<div style="aspect-ratio:${w}/${h};overflow:hidden;background:var(--imgbg)"><img src="${p.photo}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block"></div>`;
  const o=p.img||{petals:12,petal:'#e8a2b8',center:'#f6c445',bg:['#fdf6f2','#fbe9ef'],leaves:true};
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
  return `<div class="card"><div class="imgw" data-view="${p.slug}">${flowerSVG(p)}${badges(p)}<button class="wish ${wish.has(p.slug)?'on':''}" data-wish="${p.slug}">${wish.has(p.slug)?'♥':'♡'}</button><button class="quick" data-add="${p.slug}" ${p.stock<=0?'disabled style="opacity:.4"':''}>${p.stock>0?'Savatga qo‘shish':'Tugadi'}</button></div>
  <div class="pbody"><div class="cat">${cat}</div><div class="name" data-view="${p.slug}">${p.name}</div><div class="stars">★★★★★ <span>4.9 (120+)</span></div>
  <div class="prow"><span class="price">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div></div></div>`;
}
async function load(){
  const [cfg,cats]=await Promise.all([(await fetch('/api/config')).json(),(await fetch('/api/categories')).json()]);
  CFG=cfg;CATS=cats;
  const total=cats.reduce((a,c)=>a+c.total,0);
  $('#cfgLine').textContent=`${total} mahsulot • Yandex orqali 3 soatgacha yetkazish`;
  $('#delText').textContent=(cfg.delivery_note||'')+' Har kuni 08:00–22:00.';
  const c=cfg.contact;
  const ph=(c.phones||[])[0]||'+998 90 350 71 78';
  $('#hPhone').textContent=ph;$('#hPhone2').textContent=ph;
  const admins=(c.admins||[]).map(a=>`<a href="https://t.me/${a.replace('@','')}" target="_blank" style="color:var(--accent-dark);font-weight:600">${a}</a>`).join(', ');
  const phones=(c.phones||[]).map(p=>`<a href="tel:${p.replace(/\s/g,'')}" style="font-weight:600">${p}</a>`).join(', ');
  $('#contactBox').innerHTML=`Telefonlar: ${phones}<br>Manzil: ${c.address}<br>Ish vaqti: ${c.hours}<br>Adminlar: ${admins}`;
  $('#footContact').innerHTML=(c.phones||[]).map(p=>`<div class="frow"><div><a href="tel:${p.replace(/\s/g,'')}">${p}</a></div></div>`).join('')+`<div class="frow"><div>${c.address}</div></div><div class="frow"><div>${c.hours}</div></div>`;
  $('#tgBtn').href=c.telegram;$('#insBtn').href=c.instagram;
  $('#tgBtnF').href=c.telegram;$('#insBtnF').href=c.instagram;
  $('#socTg').href=c.telegram;$('#socIg').href=c.instagram;
  renderPills();await refresh(true);renderTabs();
}
function renderPills(){
  $('#pills').innerHTML=[{slug:'all',name:'Barchasi'},...CATS].map(c=>`<button class="pill ${curCat===c.slug?'on':''}" data-cat="${c.slug}">${c.name}</button>`).join('');
}
function renderCircles(){
  const box=$('#catCircles');if(!box)return;
  box.innerHTML=CATS.map(c=>{
    const rep=ALL.find(p=>p.category===c.slug)||{slug:c.slug,img:{petals:12,petal:'#e8a2b8',center:'#ffd166',bg:['#f7f7f7','#f3ece2'],leaves:true}};
    return `<div class="catcircle" data-cat="${c.slug}"><div class="im"><div>${flowerSVG(rep,200,200)}</div></div><b>${c.name}</b><small>${c.total||''} mahsulot</small></div>`;
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
      const hb1=ALL.filter(p=>p.is_featured===1).slice(0,1)[0]||ALL[0];
      const hb2=ALL.filter(p=>p.category==='toy')[0]||ALL[1]||ALL[0];
      if(hb1)$('#heroVis').innerHTML=flowerSVG(hb1,600,520);
      if(hb2&&$('#heroVis2'))$('#heroVis2').innerHTML=flowerSVG(hb2,600,520);
      const feat=ALL.filter(p=>p.is_featured===2)[0]||ALL[2]||ALL[0];
      if(feat&&$('#featImg'))$('#featImg').innerHTML=flowerSVG(feat,500,500);
      document.querySelectorAll('[data-bannerbg]').forEach((el,i)=>{
        const p=ALL.filter(x=>x.discount_pct>0)[i]||ALL[i]||ALL[0];
        if(p)el.innerHTML=flowerSVG(p,500,340);
      });
      renderTabs();initSlider();
    }
    bindCards();paintWish();
  }catch(e){$('#count').textContent='';toast("Qidiruvda xatolik — sahifani yangilab ko'ring")}
}
function bindCards(){
  document.querySelectorAll('[data-add]').forEach(b=>b.onclick=e=>{e.stopPropagation();if(!b.disabled)add(b.dataset.add)});
  document.querySelectorAll('[data-view]').forEach(el=>{el.onclick=e=>{if(e.target.closest('[data-wish]')||e.target.closest('[data-add]'))return;view(el.dataset.view)}});
  document.querySelectorAll('[data-wish]').forEach(b=>b.onclick=e=>{e.stopPropagation();toggleWish(b.dataset.wish)});
}
function toggleWish(slug){
  if(wish.has(slug)){wish.delete(slug);toast('Sevimlilardan olindi')}
  else{wish.add(slug);toast('Sevimlilarga qo‘shildi ♥')}
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
  if(!items.length){$('#cartBody').innerHTML=`<div class="empty">Savat bo'sh<br><a href="#katalog" class="btn btn-acc" style="margin-top:12px;display:inline-block" onclick="closeDrawer()">Gul tanlash</a></div>`;$('#cartFoot').innerHTML='';return}
  const sub=items.reduce((a,i)=>a+i.price*i.qty,0);
  $('#cartBody').innerHTML=items.map(i=>`<div class="citem">${flowerSVG(i,120,120)}<div><b style="font-size:13px">${i.name}</b><div style="color:var(--muted);font-size:13px">${fmt(i.price)}</div><div class="qty"><button onclick="chQty('${i.slug}',-1)">−</button><b>${i.qty}</b><button onclick="chQty('${i.slug}',1)">+</button></div></div><button class="pill" onclick="rm('${i.slug}')">✕</button></div>`).join('')
    +`<div style="border:1px dashed var(--accent-dark);padding:10px 12px;font-size:13px;color:var(--muted)">✦ ${CFG.delivery_note||"Yetkazish Yandex'ga alohida to'lanadi"}</div>`;
  $('#cartFoot').innerHTML=`<div class="row"><span>Gullar summasi:</span><b>${fmt(sub)}</b></div><div class="row"><span>Yetkazish:</span><b>Yandex alohida</b></div><div class="row ttl"><span>Jami:</span><span>${fmt(sub)}</span></div><button class="btn btn-acc" style="width:100%;margin-top:8px" onclick="openCheckout()">Buyurtma berish →</button>`;
}
window.chQty=(s,d)=>{const p=ALL.find(x=>x.slug===s);cart[s]=(cart[s]||0)+d;if(cart[s]<=0)delete cart[s];if(p&&cart[s]>p.stock)cart[s]=p.stock;localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
window.rm=s=>{delete cart[s];localStorage.setItem('aza_cart',JSON.stringify(cart));renderCart()};
async function view(slug){
  const p=await (await fetch('/api/products/'+slug)).json();window._cur=p;
  const cat=(CATS.find(c=>c.slug===p.category)||{}).name||'';
  $('#pmImg').innerHTML=flowerSVG(p,500,500)+badges(p);
  $('#pmBody').innerHTML=`<div class="cat">${cat}</div><h2>${p.name}</h2><div class="stars">★★★★★ <span>4.9 (120+)</span></div><p style="color:var(--body);line-height:1.6">${p.description}</p><div class="prow"><span class="price" style="font-size:24px">${fmt(p.price)}</span>${p.old_price?`<span class="old">${fmt(p.old_price)}</span>`:''}</div><div class="form"><div class="qty"><button onclick="mQty(-1)">−</button><b id="mq">1</b><button onclick="mQty(1)">+</button><span style="color:var(--muted);font-size:13px">Omborda: ${p.stock}</span></div><button class="btn btn-acc" style="width:100%" onclick="add('${p.slug}',+document.querySelector('#mq').textContent);closeModal('#pmodal')">Savatga qo'shish</button></div>${p.related?.length?`<h3 style="font-family:var(--serif);font-size:22px;font-weight:400;margin:16px 0 10px">Tavsiya etamiz:</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${p.related.map(r=>`<div style="border:1px solid var(--line);cursor:pointer" onclick="view('${r.slug}')">${flowerSVG(r,200,200)}<div style="padding:8px;font-size:12px">${r.name}<br><b>${fmt(r.price)}</b></div></div>`).join('')}</div>`:''}`;
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
/* SAMA uslubidagi checkout: manzil + yetkazish + to'lov + prepay + promokod */
const CO={ship:'standard',pay:'cash',promo:{code:'',pct:0},loc:null};
/* SAMA uslubidagi auto-fill: akkaunt + oxirgi buyurtma eslab qolinadi */
function escA(s){return String(s||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}
function coProfile(){
  let p={}; try{p=JSON.parse(localStorage.getItem('aza_profile')||'{}')}catch(e){p={}}
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
const SHIP_LABEL={standard:'Standart (Yandex, 3 soat)',express:'Tezkor (1 soat)'};
const PAY_LABEL={cash:"Naqd / yetkazib berishda",card:'Plastik karta (terminal)',online:"Online to'lov (Click / Payme)"};
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
window.openCheckout=()=>{
  if(!cartItems().length)return;
  CO.ship='standard';CO.pay='cash';CO.promo={code:'',pct:0};
  renderCheckout();closeDrawer();openModal('#cmodal');
};
function renderCheckout(){
  const t=coTotals();
  const regions=CFG.regions||['Toshkent shahri'];
  const pr=coProfile();
  const ships=CFG.ship||[{slug:'standard',name:'Standart',hint:"Yandex orqali 3 soatgacha · alohida to'lanadi"},{slug:'express',name:'Tezkor',hint:'1 soatda · +30 000 so‘m'}];
  const card=CFG.pay_card||'';
  $('#coBody').innerHTML=`
  <h2 style="margin:0;font-family:var(--serif);font-size:30px;font-weight:400">Buyurtmani rasmiylashtirish</h2>
  <p style="color:var(--muted);font-size:13.5px">Buyurtma uchun <b>50% oldindan to'lov</b> qilinadi.</p>
  <div class="cform" style="margin-top:14px">
    <div><h3>Aloqa ma'lumotlari</h3><div class="fgrid2" style="margin-top:10px">
      <label class="fld"><span>Ism *</span><input id="fName" value="${escA(pr.name)}"></label>
      <label class="fld"><span>Telefon *</span><input id="fPhone" inputmode="tel" placeholder="+998 __ ___ __ __" value="${escA(pr.phone)}"></label>
    </div></div>
    <div><h3>Yetkazib berish manzili</h3><div class="fgrid2" style="margin-top:10px">
      <label class="fld"><span>Hudud *</span><select id="fRegion">${regions.map(r=>`<option ${pr.region===r?'selected':''}>${r}</option>`).join('')}</select></label>
      <label class="fld"><span>Tuman / shahar *</span><input id="fCity" placeholder="Masalan: Chilonzor" value="${escA(pr.city)}"></label>
      <label class="fld full"><span>Manzil (ko'cha, uy) *</span><input id="fAddr" placeholder="Masalan: Bunyodkor shoh ko'chasi 12" value="${escA(pr.address)}"></label>
      <label class="fld full"><span>Izoh (kuryer uchun)</span><input id="fNote" placeholder="Masalan: 2-qavat, tabriknoma matni..." value="${escA(pr.note)}"></label>
    </div></div>
    <div><h3>Yetkazish usuli</h3><div class="radio-cards" style="margin-top:10px" id="coShip">
      ${ships.map(s=>`<label class="radio-card"><input type="radio" name="ship" value="${s.slug}" ${CO.ship===s.slug?'checked':''}><span><b>${s.name}</b><small>${s.hint}</small></span></label>`).join('')}
    </div></div>
    <div><h3>To'lov usuli</h3><div class="radio-cards" style="margin-top:10px" id="coPay">
      <label class="radio-card"><input type="radio" name="pay" value="cash" checked><span><b>Naqd / yetkazib berishda</b><small>Kuryerga naqd to'lov</small></span></label>
      <label class="radio-card"><input type="radio" name="pay" value="card"><span><b>Plastik karta</b><small>Yetkazib berishda terminal</small></span></label>
      <label class="radio-card"><input type="radio" name="pay" value="online"><span><b>Online to'lov</b><small>Payme / Click</small></span></label>
    </div></div>
    <div class="prepay" id="coPrepay"></div>
    <div><h3>Promokod (% li chegirma)</h3>
      <div class="promo-row" style="margin-top:10px"><input id="promoInput" placeholder="Promokodni kiriting"><button class="btn btn-outline" id="promoBtn" style="padding:12px 22px">Qo'llash</button></div>
      <p class="promo-msg" id="promoMsg"></p>
    </div>
    <div id="coSummary"></div>
    <button class="btn btn-acc" id="sendOrder" style="width:100%">Buyurtmani tasdiqlash →</button>
    <p class="hint">🔒 Ma'lumotlaringiz xavfsiz saqlanadi</p>
  </div>`;
  document.querySelectorAll('#coShip input').forEach(r=>r.onchange=()=>{CO.ship=r.value;refreshCo()});
  document.querySelectorAll('#coPay input').forEach(r=>r.onchange=()=>{CO.pay=r.value});
  $('#promoBtn').onclick=applyPromo;
  $('#sendOrder').onclick=submitOrder;
  refreshCo();
  maskPhone($('#fPhone'));
  setTimeout(initCoMap,120);
}
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
  const fm=document.getElementById('findMe');
  if(fm)fm.onclick=()=>{
    if(!navigator.geolocation)return toast('Geolokatsiya topilmadi');
    toast('Joylashuv aniqlanmoqda...');
    navigator.geolocation.getCurrentPosition(p=>{
      placeCoLoc(p.coords.latitude,p.coords.longitude);
      coMap.setView([p.coords.latitude,p.coords.longitude],15);
    },()=>toast('Ruxsat berilmadi — xaritani bosing 📍'),{timeout:10000});
  };
}
function placeCoLoc(lat,lon){
  CO.loc={lat:+lat.toFixed(6),lon:+lon.toFixed(6)};
  if(coMarker)coMarker.setLatLng([lat,lon]);
  else coMarker=L.marker([lat,lon]).addTo(coMap);
  const mc=document.getElementById('mapCoords');
  if(mc)mc.textContent=`📍 ${CO.loc.lat}, ${CO.loc.lon}`;
}
function refreshCo(){
  const t=coTotals();
  const pct=CFG.prepay_pct||50;
  const card=CFG.pay_card||'';
  $('#coPrepay').innerHTML=`<span class="pl">Oldindan to'lov · ${pct}%</span><div class="big">${fmt(t.prepay)}</div>
  <div class="rest">Qolgan <b>${fmt(t.rest)}</b> yetkazib berishda to'lanadi</div>
  <div class="cardn">${card?`💳 To'lov kartasi (Click / Payme):<br><code id="payCardNum">${card}</code><br><small>To'lov chekini saqlang — operator tasdiqlaydi.</small>`:`💳 To'lov kartasi: operatorimiz sizga shu chat orqali yuboradi.`}</div>`;
  const pc=$('#payCardNum');if(pc)pc.onclick=()=>{try{navigator.clipboard.writeText(card);toast('Karta nusxalandi')}catch(e){}};
  $('#coSummary').innerHTML=t.items.map(i=>`<div class="sumrow"><span>${i.name} × ${i.qty}</span><b>${fmt(i.price*i.qty)}</b></div>`).join('')
    +`<div class="sumrow"><span>Mahsulotlar</span><b>${fmt(t.sub)}</b></div>`
    +(t.disc?`<div class="sumrow"><span>Promokod ${CO.promo.code} (−${CO.promo.pct}%)</span><b>−${fmt(t.disc)}</b></div>`:'')
    +`<div class="sumrow"><span>Yetkazish (${SHIP_LABEL[CO.ship]||CO.ship})</span><b>${t.ship?fmt(t.ship):"Yandex alohida"}</b></div>`
    +`<div class="sumrow total"><span>Jami</span><b>${fmt(t.total)}</b></div>`
    +`<div class="sumrow pre"><span>Oldindan ${pct}%</span><b>${fmt(t.prepay)}</b></div>`;
}
async function applyPromo(){
  const inp=$('#promoInput'),msg=$('#promoMsg');
  const code=(inp.value||'').trim().toUpperCase();
  if(!code){CO.promo={code:'',pct:0};msg.textContent='';msg.className='promo-msg';refreshCo();return}
  msg.textContent='Tekshirilmoqda...';msg.className='promo-msg';
  try{
    const r=await fetch('/api/promo?code='+encodeURIComponent(code));
    if(r.status===404){msg.textContent='⛔ Promokod server restartdan keyin ishlaydi';msg.className='promo-msg err';return}
    const j=await r.json();
    if(j.ok){CO.promo={code:j.code,pct:j.pct};msg.textContent=`✅ ${j.pct}% chegirma qo'llandi!`;msg.className='promo-msg ok'}
    else{CO.promo={code:'',pct:0};msg.textContent='⛔ '+(j.error||'topilmadi');msg.className='promo-msg err'}
  }catch(e){msg.textContent='⛔ Tekshirib bo‘lmadi';msg.className='promo-msg err'}
  refreshCo();
}
async function submitOrder(){
  const body={name:$('#fName').value.trim(),phone:$('#fPhone').value.trim(),
    region:$('#fRegion').value,city:$('#fCity').value.trim(),address:$('#fAddr').value.trim(),
    note:$('#fNote').value.trim(),ship:CO.ship,pay:CO.pay,promo:CO.promo.code,
    items:cartItems().map(i=>({slug:i.slug,qty:i.qty}))};
  if(body.name.length<2)return toast('Ismingizni yozing');
  if(body.phone.replace(/\D/g,'').length<9)return toast('Telefonni to‘g‘ri kiriting');
  if(body.city.length<2)return toast('Tuman / shaharni yozing');
  if(body.address.length<5&&!CO.loc)return toast('Manzilni yozing yoki xaritadan belgilang 📍');
  if(!body.items.length)return toast('Savat bo‘sh');
  saveProfile({name:body.name,phone:body.phone,region:body.region,city:body.city,address:body.address,note:body.note});
  body.lat=CO.loc?CO.loc.lat:null; body.lon=CO.loc?CO.loc.lon:null;
  try{
    let r=await fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(body)});
    if(r.status===404){
      // server hali restart qilinmagan — eski API orqali yuboramiz
      const legacy={name:body.name,phone:body.phone,
        address:[body.region,body.city,body.address].filter(Boolean).join(', ')+(CO.loc?' (xaritada belgilangan 📍)':''),
        comment:[body.note,'Yetkazish: '+(SHIP_LABEL[body.ship]||body.ship),'To‘lov: '+(PAY_LABEL[body.pay]||body.pay)].filter(Boolean).join(' | '),
        items:body.items};
      r=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(legacy)});
      const lo=await r.json();
      if(!r.ok)return toast('Xatolik: '+(lo.detail||'qayta urining'));
      cart={};localStorage.setItem('aza_cart','{}');renderCart();closeModal('#cmodal');
      toast(`Rahmat! Buyurtma #${lo.order_id} qabul qilindi. Jami: ${fmt(lo.total)}`);
      return;
    }
    const o=await r.json();
    if(!r.ok)return toast('Xatolik: '+(o.detail||'qayta urining'));
    cart={};localStorage.setItem('aza_cart','{}');renderCart();
    showSuccess(o,body);
  }catch(e){toast('Xatolik — internetni tekshiring')}
}
function showSuccess(o,form){
  const botUrl=o.bot_url||'https://t.me/azaflowers';
  $('#coBody').innerHTML=`<div style="text-align:center;padding:10px 0">
    <div style="font-size:52px">✓</div>
    <h2 style="font-family:var(--serif);font-weight:400;font-size:30px;margin:8px 0">Buyurtmangiz qabul qilindi!</h2>
    <p style="color:var(--body)">Rahmat, <b>${form.name}</b>. Buyurtma raqami: <b>${o.no||('#'+o.order_id)}</b></p>
    <div style="text-align:left;border:1px solid var(--line);padding:16px;margin:16px 0">
      <div class="sumrow"><span>Manzil</span><b>${[form.region,form.city,form.address].filter(Boolean).join(', ')}</b></div>
      <div class="sumrow"><span>To'lov</span><b>${PAY_LABEL[form.pay]||form.pay}</b></div>
      ${form.promo?`<div class="sumrow"><span>Promokod</span><b>${form.promo}</b></div>`:''}
      <div class="sumrow total"><span>Jami</span><b>${fmt(o.total)}</b></div>
      <div class="sumrow pre"><span>Oldindan to'lov</span><b>${fmt(o.prepay)}</b></div>
    </div>
    <div id="coStatus"></div>
    <h3 style="font-family:var(--serif);font-weight:400;font-size:22px;margin:14px 0 6px">Keyingi qadam — to'lov 💳</h3>
    <p style="color:var(--body);font-size:14px"><b>${fmt(o.prepay)}</b> ni to'lang va chekni botga yuboring.</p>
    <a class="btn btn-acc" style="width:100%;margin-top:8px" target="_blank" href="${botUrl}">✈ Botga o'tish va chek yuborish</a>
    <p class="hint">⚠️ Aynan <b>${fmt(o.prepay)}</b> to'lang — ko'p ham, kam ham emas.</p>
  </div>`;
  pollOrder(o.id||o.order_id,0);
}
async function pollOrder(oid,n){
  if(n>60||!document.getElementById('coStatus'))return;
  try{
    const r=await fetch('/api/order?id='+oid);
    if(!r.ok)return;
    const j=await r.json();
    const box=document.getElementById('coStatus');if(!box)return;
    const st=j.status;
    if(st==='awaiting_confirm')box.innerHTML=`<div class="prepay" style="margin-top:10px"><b>📸 Chek qabul qilindi!</b><br><span style="font-size:13.5px">Admin tekshirmoqda...</span></div>`;
    else if(['accepted','qabul','preparing','delivering'].includes(st)){box.innerHTML=`<div class="prepay" style="margin-top:10px"><b>✓ Buyurtma qabul qilindi, rahmat! 🎉</b><br><span style="font-size:13.5px">To'lovingiz tasdiqlandi.</span></div>`;return}
    else if(['rejected','cancelled'].includes(st)){box.innerHTML=`<div class="prepay" style="margin-top:10px;border-color:var(--sale)"><b>❌ Buyurtma tasdiqlanmadi</b><br><span style="font-size:13.5px">Chekda muammo — qayta urinib ko'ring.</span></div>`;return}
  }catch(e){}
  setTimeout(()=>pollOrder(oid,n+1),5000);
}

/* slider */
let curSlide=0,slideTimer=null;
function showSlide(i){
  const slides=document.querySelectorAll('.slide');if(!slides.length)return;
  curSlide=(i+slides.length)%slides.length;
  slides.forEach((s,k)=>s.classList.toggle('on',k===curSlide));
  document.querySelectorAll('#slideDots button').forEach((d,k)=>d.classList.toggle('on',k===curSlide));
}
function initSlider(){
  const slides=document.querySelectorAll('.slide');
  const dots=$('#slideDots');
  if(dots&&!dots.innerHTML)dots.innerHTML=[...slides].map((_,k)=>`<button data-dot="${k}" class="${k===0?'on':''}"></button>`).join('');
  dots.onclick=e=>{const b=e.target.closest('[data-dot]');if(b){showSlide(+b.dataset.dot);restartAuto()}};
  $('#slidePrev').onclick=()=>{showSlide(curSlide-1);restartAuto()};
  $('#slideNext').onclick=()=>{showSlide(curSlide+1);restartAuto()};
  restartAuto();
}
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
$('#wishBtn').onclick=()=>{
  if(!wish.size)return toast('Sevimlilar bo‘sh — ♡ bosing');
  const list=ALL.filter(p=>wish.has(p.slug));
  $('#grid').innerHTML=list.map(card).join('');bindCards();
  document.getElementById('katalog').scrollIntoView({behavior:'smooth'});
  toast(`${list.length} ta sevimli ko'rsatildi`);
};
$('#fWish').onclick=e=>{e.preventDefault();$('#wishBtn').click()};
$('#fCart').onclick=e=>{e.preventDefault();openDrawer()};
/* sendOrder endi renderCheckout ichida bind qilinadi (SAMA uslubi) */
load().then(async()=>{await loadMe();paintAuth();renderCart();paintWish()});
document.getElementById('tabLogin').onclick=()=>switchTab('login');
document.getElementById('tabReg').onclick=()=>switchTab('reg');
document.getElementById('doLogin').onclick=()=>{const ph=document.getElementById('lPhone').value.trim(),pw=document.getElementById('lPass').value;if(ph.length<7||!pw)return toast('Telefon va parolni kiriting');doAuth('/api/auth/login',{phone:ph,password:pw})};
document.getElementById('doReg').onclick=()=>{const nm=document.getElementById('rName').value.trim(),ph=document.getElementById('rPhone').value.trim(),pw=document.getElementById('rPass').value;if(nm.length<2||ph.length<7||pw.length<4)return toast("Ma'lumotlarni to'liq kiriting");doAuth('/api/auth/register',{name:nm,phone:ph,password:pw})};
if(location.hash==='#kirish')openModal('#amodal');
