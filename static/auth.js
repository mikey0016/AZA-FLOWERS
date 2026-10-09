// Sub-sahifalar (about/track/cabinet) uchun umumiy auth + footer
const Auth = {
  get token() { return localStorage.getItem('aza_token'); },
  headers() { const t = this.token; return t ? { 'Authorization': 'Bearer ' + t } : {}; },
  save(t, u) { localStorage.setItem('aza_token', t); localStorage.setItem('aza_user', JSON.stringify(u)); },
  clear() { localStorage.removeItem('aza_token'); localStorage.removeItem('aza_user'); },
  cached() { try { return JSON.parse(localStorage.getItem('aza_user') || 'null'); } catch (e) { return null; } },
  async me() {
    const t = this.token; if (!t) return null;
    try {
      const r = await fetch('/api/auth/me', { headers: this.headers() });
      if (!r.ok) { this.clear(); return null; }
      const u = await r.json();
      localStorage.setItem('aza_user', JSON.stringify(u));
      return u;
    } catch (e) { return this.cached(); }
  }
};
async function paintAuth() {
  const el = document.getElementById('authArea'); if (!el) return;
  const u = Auth.cached() || await Auth.me();
  if (u) {
    el.innerHTML = `<a class="pill" href="/cabinet">${u.name.split(' ')[0]} → Kabinet</a> <button class="pill" id="loBtn">Chiqish</button>`;
    document.getElementById('loBtn').onclick = async () => {
      try { await fetch('/api/auth/logout', { method: 'POST', headers: Auth.headers() }); } catch (e) {}
      Auth.clear(); location.reload();
    };
  } else {
    el.innerHTML = `<a class="pill" href="/#kirish">Kirish</a>`;
  }
}
async function fillFooter() {
  try {
    const [cfg, cats] = await Promise.all([(await fetch('/api/config')).json(), (await fetch('/api/categories')).json()]);
    const fc = document.getElementById('footCats');
    if (fc) fc.innerHTML = cats.map(x => `<a href="/#katalog">${x.name}</a>`).join('');
    const c = cfg.contact, ft = document.getElementById('footContact');
    if (ft) ft.innerHTML = (c.phones || []).map(p => `<div class="frow"><div><a href="tel:${p.replace(/\s/g, '')}">${p}</a></div></div>`).join('')
      + `<div class="frow"><div>${c.address}</div></div><div class="frow"><div>${c.hours}</div></div>`;
    for (const [id, key] of [['tgBtnF', 'telegram'], ['insBtnF', 'instagram']]) {
      const e = document.getElementById(id); if (e) e.href = c[key];
    }
  } catch (e) {}
}
paintAuth(); fillFooter();
