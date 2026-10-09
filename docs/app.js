/* AZA FLOWERS — GitHub Pages static version (no backend).
   Katalog data.json dan o'qiladi, savat localStorage, buyurtma Telegram orqali. */
'use strict';
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
let ALL = [], CATS = [], CFG = { delivery_note: '', contact: {} }, curCat = 'all';
let cart = {};
try { cart = JSON.parse(localStorage.getItem('aza_cart') || '{}'); } catch (e) { cart = {}; }

const fmt = n => (Number(n) || 0).toLocaleString('uz-UZ').replace(/,/g, ' ') + " so'm";
function toast(m) {
  const t = $('#toast'); if (!t) return;
  t.textContent = m; t.classList.add('show');
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 3000);
}

const U = (id, w = 800) => `https://images.unsplash.com/${id}?q=80&w=${w}&auto=format&fit=crop`;
const LOCAL_BUKET = './uploads/mavsumiy-aralash-buket_1791556816.jpg';
const PHOTOS = {
  buketlar: LOCAL_BUKET,
  atirgullar: U('photo-1518895949257-7621c3c786d7'),
  kompozitsiyalar: U('photo-1508610048659-a06b669e3321'),
  sovgalar: U('photo-1526047932273-341f2a7631f9'),
  xonalar: U('photo-1485955900006-10f4d324d411'),
  toy: U('photo-1522673607200-164d1b6ce486'),
};
const BY_SLUG = {
  'million-atirgul': U('photo-1518895949257-7621c3c786d7'),
  'qizil-atirgul-25': U('photo-1494972308805-463bc619d34e'),
  'oq-atirgul-kompozitsiya': U('photo-1508610048659-a06b669e3321'),
  'pushti-lolalar': U('photo-1520763185298-1b434c919102'),
  'bahor-savati': U('photo-1526047932273-341f2a7631f9'),
  'kungaboqar-quvonchi': U('photo-1470509037663-253afd7f0f51'),
  'pionlar-nafosati': U('photo-1591886960571-74d43a9d4166'),
  'orkide-kompozitsiya': U('photo-1610397648930-477b8c7f0943'),
  'shokolad-atirgul-sovga': U('photo-1549007994-cb92caebd54b'),
  'toy-buketi-oq-bulut': U('photo-1522673607200-164d1b6ce486'),
  'fikus-xona-uchun': U('photo-1485955900006-10f4d324d411'),
  'sukkulentlar-toplami': U('photo-1459156212016-c812468e2115'),
  'gul-barglari-yolagi': U('photo-1490750967868-88aa4486c946'),
  'mavsumiy-aralash-buket': U('photo-1490750967868-88aa4486c946'),
};
const imgFor = (p, w = 800) => {
  let ph = p.photo || '';
  if (ph.startsWith('/static/uploads/')) ph = '.' + ph.replace('/static', '');
  if (ph.startsWith('/static/')) ph = '.' + ph;
  if (ph) return ph;
  return BY_SLUG[p.slug] || PHOTOS[p.category] || PHOTOS.buketlar;
};
function flowerImg(p, w = 800, cls = 'pimg') {
  const src = imgFor(p, w);
  const esc = (p.name || '').replace(/"/g, '');
  return `<img class="${cls}" src="${src}" alt="${esc}" loading="lazy" onerror="this.onerror=null;this.src='${PHOTOS.buketlar}'">`;
}
function badges(p) {
  let b = '';
  if (p.discount_pct) b += `<span class="td">-${p.discount_pct}%</span>`;
  if (p.is_featured === 1) b += `<span class="tt">TOP</span>`;
  if (p.is_featured === 2) b += `<span class="tn">YANGI</span>`;
  return b ? `<div class="tag">${b}</div>` : '';
}
const stars = () => `<div class="rating">★★★★★ <span>4.9 (120+)</span></div>`;
const qtyOf = slug => cart[slug] || 0;
const CACHE = {};
const cachePut = p => { if (p && p.slug) CACHE[p.slug] = p; };
const findP = slug => CACHE[slug] || ALL.find(x => x.slug === slug) || window._cur;

function footHTML(p) {
  if (p.stock <= 0) return `<button class="add" disabled>Mavjud emas</button>`;
  const q = qtyOf(p.slug);
  if (!q) return `<button class="add" data-act="add" data-slug="${p.slug}">🛒 Savatga qo'shish</button>`;
  return `<div class="stepper" data-foot-step="${p.slug}">
    <button data-act="dec" data-slug="${p.slug}" aria-label="kamaytirish">−</button>
    <b>${q} dona</b>
    <button data-act="inc" data-slug="${p.slug}" aria-label="ko'paytirish">+</button>
  </div>`;
}
function card(p) {
  const cat = (CATS.find(c => c.slug === p.category) || {}).name || p.category;
  const out = p.stock <= 0;
  return `<div class="card"><div class="imgw" data-act="view" data-slug="${p.slug}">${flowerImg(p, 700)}${badges(p)}<span class="stock ${out ? 'out' : ''}">${out ? '❌ Tugadi' : '🟢 ' + p.stock + ' dona'}</span></div>
  <div class="pbody"><div class="cat">${cat}</div><div class="name" data-act="view" data-slug="${p.slug}">${p.name}</div>${stars()}
  <div class="prow"><span class="price">${fmt(p.price)}</span>${p.old_price ? `<span class="old">${fmt(p.old_price)}</span>` : ''}</div>
  <div data-foot="${p.slug}">${footHTML(p)}</div></div></div>`;
}
function refreshFoots(slug) {
  const p = findP(slug); if (!p || !slug) return;
  try {
    $$(`[data-foot="${CSS.escape(slug)}"]`).forEach(el => { el.innerHTML = footHTML(p); });
  } catch (e) {
    $$(`[data-foot="${slug}"]`).forEach(el => { el.innerHTML = footHTML(p); });
  }
}

function saveCart() { localStorage.setItem('aza_cart', JSON.stringify(cart)); }
function setQty(slug, q) {
  const p = findP(slug);
  q = Math.max(0, Math.min(p ? p.stock : 50, q));
  if (q <= 0) delete cart[slug]; else cart[slug] = q;
  saveCart(); renderCart(); refreshFoots(slug);
}
function addTo(slug, n = 1) {
  const p = findP(slug); if (!p || p.stock <= 0) return;
  setQty(slug, qtyOf(slug) + n);
  toast("Savatga qo'shildi 🌷");
}
function cartItems() {
  return Object.entries(cart)
    .map(([slug, qty]) => { const p = CACHE[slug] || ALL.find(x => x.slug === slug); return p ? { ...p, qty } : null; })
    .filter(Boolean);
}
function renderCart() {
  const nEl = $('#cartN'); if (!nEl) return;
  const items = cartItems(), n = items.reduce((a, i) => a + i.qty, 0);
  nEl.textContent = n;
  if (!items.length) {
    $('#cartBody').innerHTML = `<div class="empty">🧺 Savat bo'sh<br><a href="#katalog" class="btn btn-p" style="margin-top:12px;display:inline-block;padding:12px 24px" data-act="close-drawer">Gul tanlash 💐</a></div>`;
    $('#cartFoot').innerHTML = ''; return;
  }
  const sub = items.reduce((a, i) => a + i.price * i.qty, 0);
  $('#cartBody').innerHTML = items.map(i => `<div class="citem">${flowerImg(i, 200)}<div><b>${i.name}</b><div style="color:var(--muted);font-size:13px">${fmt(i.price)}</div><div class="qty"><button data-act="cdec" data-slug="${i.slug}">−</button><b>${i.qty}</b><button data-act="cinc" data-slug="${i.slug}">+</button></div></div><button class="pill" style="padding:7px 12px" data-act="rm" data-slug="${i.slug}">✕</button></div>`).join('')
    + `<div style="border:1.5px dashed var(--line2);border-radius:12px;padding:10px 12px;font-size:13px;color:var(--muted);background:#0e0c09">🚚 ${CFG.delivery_note || "Yetkazish Yandex'ga alohida to'lanadi"}</div>`;
  $('#cartFoot').innerHTML = `<div class="row"><span>Gullar summasi:</span><b>${fmt(sub)}</b></div><div class="row"><span>Yetkazish:</span><b>Yandex alohida</b></div><div class="row ttl"><span>Jami:</span><span>${fmt(sub)}</span></div><button class="btn btn-p" style="width:100%;margin-top:8px" data-act="checkout">Buyurtma berish →</button>`;
}

function openModal(s) { $(s).classList.add('show'); $('#overlay').classList.add('show'); }
function closeModal(s) {
  $(s).classList.remove('show');
  if (!$('#drawer').classList.contains('show')) $('#overlay').classList.remove('show');
}
function closeAll() {
  ['#pmodal', '#cmodal'].forEach(s => { const m = $(s); if (m) m.classList.remove('show'); });
  closeDrawer();
}
function openDrawer() { $('#drawer').classList.add('show'); $('#overlay').classList.add('show'); renderCart(); }
function closeDrawer() {
  $('#drawer').classList.remove('show');
  if (!['#pmodal', '#cmodal'].some(s => $(s) && $(s).classList.contains('show')))
    $('#overlay').classList.remove('show');
}

function view(slug) {
  const p = findP(slug);
  if (!p) { toast('Mahsulot topilmadi'); return; }
  window._cur = p;
  const rel = ALL.filter(x => x.category === p.category && x.slug !== p.slug).slice(0, 4);
  const cat = (CATS.find(c => c.slug === p.category) || {}).name || '';
  $('#pmImg').innerHTML = flowerImg(p, 900);
  $('#pmBody').innerHTML = `<div class="cat">${cat}</div><h2 style="margin:6px 0;font-size:32px;font-family:Manrope;font-weight:800">${p.name}</h2>${stars()}<p style="color:var(--muted);line-height:1.65">${p.description || ''}</p><div class="prow"><span class="price" style="font-size:24px">${fmt(p.price)}</span>${p.old_price ? `<span class="old">${fmt(p.old_price)}</span>` : ''}</div><div style="background:#1c1610;border:1px solid var(--line);border-radius:12px;padding:10px 14px;font-size:13px;color:var(--muted);margin-top:10px">📦 Omborda: <b style="color:var(--ink)">${p.stock} dona</b> • 🚚 Yandex 3 soatda</div><div class="form"><div class="qty"><button data-act="mq" data-d="-1">−</button><b id="mq">1</b><button data-act="mq" data-d="1">+</button></div><button class="btn btn-p" data-act="madd" data-slug="${p.slug}">🛒 Savatga qo'shish</button></div>${rel.length ? `<h3 style="margin:18px 0 10px">Tavsiya etamiz:</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${rel.map(r => `<div style="border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;background:#1c1610" data-act="view" data-slug="${r.slug}">${flowerImg(r, 400)}<div style="padding:8px;font-size:12px;font-weight:700">${r.name}<br><span style="color:var(--gold-deep)">${fmt(r.price)}</span></div></div>`).join('')}</div>` : ''}`;
  openModal('#pmodal');
}

function renderPills() {
  $('#pills').innerHTML = [{ slug: 'all', name: '✨ Barchasi' }, ...CATS]
    .map(c => `<button class="pill ${curCat === c.slug ? 'on' : ''}" data-act="cat" data-slug="${c.slug}">${c.name}</button>`).join('');
}
function renderCats() {
  const g = $('#catGrid'); if (!g) return;
  const counts = {};
  ALL.forEach(p => { counts[p.category] = (counts[p.category] || 0) + 1; });
  g.innerHTML = CATS.map(c => `<button class="catcard" data-act="catgo" data-slug="${c.slug}"><img src="${PHOTOS[c.slug] || PHOTOS.buketlar}" loading="lazy" alt="${c.name}" onerror="this.onerror=null;this.src='${LOCAL_BUKET}'"><div class="cb"><b>${c.name}</b><small>${counts[c.slug] || 0} ta mahsulot →</small></div></button>`).join('');
}
function applyFilter() {
  const q = ($('#q').value || '').trim().toLowerCase(), sort = $('#sort').value;
  let list = ALL.slice();
  if (curCat !== 'all') list = list.filter(p => p.category === curCat);
  if (q) list = list.filter(p => p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q));
  if (sort === 'cheap') list.sort((a, b) => a.price - b.price);
  else if (sort === 'expensive') list.sort((a, b) => b.price - a.price);
  else if (sort === 'discount') list.sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0));
  else list.sort((a, b) => ((-b.is_featured) - (-a.is_featured)) || (a.price - b.price));
  $('#grid').innerHTML = list.map(card).join('') || `<div class="empty">😕 Hech narsa topilmadi<br>Qidiruvni o'zgartirib ko'ring</div>`;
  $('#count').textContent = q ? `"${q}" — ${list.length} ta topildi` : list.length + ' ta mahsulot';
}
function refreshTop() {
  const top = ALL.filter(p => p.is_featured || p.discount_pct).slice(0, 4);
  $('#topGrid').innerHTML = (top.length ? top : ALL.slice(0, 4)).map(card).join('');
}

async function load() {
  const r = await fetch('./data.json');
  if (!r.ok) throw new Error('data');
  const d = await r.json();
  CFG = { delivery_note: d.delivery_note, contact: d.contact };
  CATS = d.categories.map(c => ({ ...c, total: d.products.filter(p => p.category === c.slug).length }));
  ALL = d.products;
  ALL.forEach(cachePut);
  $('#cfgLine').textContent = `${ALL.length} mahsulot • Yandex orqali 3 soatgacha yetkazish`;
  $('#delText').textContent = (CFG.delivery_note || '') + ' Har kuni 08:00–22:00.';
  const c = CFG.contact || {};
  const phones = (c.phones || []).map(p => `<a href="tel:${p.replace(/\s/g, '')}" style="color:var(--gold-deep);font-weight:700">${p}</a>`).join(', ');
  $('#contactBox').innerHTML = `Telefonlar: ${phones}<br>Manzil: ${c.address || ''}<br>Ish vaqti: ${c.hours || ''}`;
  $('#footContact').innerHTML = (c.phones || []).map(p => `<div class="frow"><div>📞 <a href="tel:${p.replace(/\s/g, '')}">${p}</a></div></div>`).join('') + `<div class="frow"><div>📍 ${c.address || ''}</div></div><div class="frow"><div>🕗 ${c.hours || ''}</div></div>`;
  $('#footCats').innerHTML = CATS.map(x => `<a href="#katalog" data-act="catgo" data-slug="${x.slug}">${x.name}</a>`).join('');
  $('#tgBtn').href = c.telegram || '#'; $('#insBtn').href = c.instagram || '#';
  $('#tgBtnF').href = c.telegram || '#'; $('#insBtnF').href = c.instagram || '#';
  const auth = $('#authArea');
  if (auth) auth.innerHTML = `<a class="pill" href="${c.telegram || '#'}" target="_blank">✈️ Telegram</a>`;
  renderPills(); renderCats(); applyFilter(); refreshTop();
}

function validPhone(ph) {
  const d = (ph || '').replace(/\D/g, '');
  return d.length >= 9 && (d.startsWith('998') ? d.length === 12 : true);
}
function sendOrder(btn) {
  const name = $('#fName').value.trim(), phone = $('#fPhone').value.trim(),
    addr = $('#fAddr').value.trim(), com = $('#fCom').value.trim();
  const items = cartItems();
  if (name.length < 2) return toast('Ismingizni yozing');
  if (!validPhone(phone)) return toast('Telefonni to‘liq yozing (+998 ...)');
  if (addr.length < 5) return toast('Manzilni yozing');
  if (!items.length) return toast('Savat bo‘sh');
  const sub = items.reduce((a, i) => a + i.price * i.qty, 0);
  const lines = items.map(i => `• ${i.name} — ${i.qty} dona — ${fmt(i.price * i.qty)}`).join('\n');
  const msg = `🌷 AZA FLOWERS — yangi buyurtma (sayt)\n👤 ${name}\n📞 ${phone}\n📍 ${addr}\n💬 ${com || '-'}\n\n${lines}\n\nJami: ${fmt(sub)}\nYetkazish: Yandex alohida`;
  try { navigator.clipboard.writeText(msg).catch(() => {}); } catch (e) {}
  const tg = (CFG.contact && CFG.contact.telegram) || 'https://t.me/azaflowers';
  window.open(tg, '_blank');
  toast('Buyurtma matni nusxalandi — Telegramda yuboring 🌷');
  closeModal('#cmodal');
}
function openCheckout() {
  const items = cartItems(); if (!items.length) return;
  const sub = items.reduce((a, i) => a + i.price * i.qty, 0);
  $('#sumLine').textContent = `${items.length} tur • Gullar: ${fmt(sub)}. Yetkazish Yandex'ga alohida to'lanadi.`;
  closeDrawer(); openModal('#cmodal');
}

document.addEventListener('click', e => {
  const t = e.target.closest('[data-act]');
  if (e.target.id === 'overlay') { closeAll(); return; }
  const closer = e.target.closest('[data-close]');
  if (closer) { closeAll(); return; }
  if (!t) return;
  const act = t.dataset.act, slug = t.dataset.slug;
  if (act === 'add') { e.stopPropagation(); addTo(slug, 1); }
  else if (act === 'inc') { e.stopPropagation(); addTo(slug, 1); }
  else if (act === 'dec') { e.stopPropagation(); setQty(slug, qtyOf(slug) - 1); }
  else if (act === 'view') { view(slug); }
  else if (act === 'cat') { curCat = slug; renderPills(); applyFilter(); }
  else if (act === 'catgo') { curCat = slug; renderPills(); applyFilter(); const k = $('#katalog'); if (k) k.scrollIntoView({ behavior: 'smooth' }); }
  else if (act === 'cinc') setQty(slug, qtyOf(slug) + 1);
  else if (act === 'cdec') setQty(slug, qtyOf(slug) - 1);
  else if (act === 'rm') setQty(slug, 0);
  else if (act === 'mq') { const m = $('#mq'); if (m) m.textContent = Math.max(1, Math.min(20, +m.textContent + (+t.dataset.d))); }
  else if (act === 'madd') { addTo(slug, +($('#mq') ? $('#mq').textContent : 1)); closeModal('#pmodal'); }
  else if (act === 'checkout') openCheckout();
  else if (act === 'close-drawer') closeDrawer();
  else if (act === 'send-order') sendOrder(t);
});

let qt;
function bindSearch() {
  const q = $('#q'); if (!q || q._bound) return; q._bound = true;
  q.addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(applyFilter, 300); });
  q.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); clearTimeout(qt); applyFilter(); } });
  const s = $('#sort'); if (s && !s._bound) { s._bound = true; s.addEventListener('change', applyFilter); }
  const oc = $('#openCart'); if (oc && !oc._bound) { oc._bound = true; oc.addEventListener('click', openDrawer); }
  const cc = $('#closeCart'); if (cc && !cc._bound) { cc._bound = true; cc.addEventListener('click', closeDrawer); }
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeAll(); });
}

window.addTo = addTo; window.view = view;
document.addEventListener('DOMContentLoaded', () => {
  bindSearch();
  renderCart();
  load().catch(() => toast("Ma'lumot yuklanmadi — internetni tekshiring"));
});
