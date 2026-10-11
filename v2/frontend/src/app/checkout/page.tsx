"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { REGIONS, EXPRESS_FEE, createOrder, validateCoupon } from "@/lib/api";
import { uzs } from "@/lib/format";
import { useShop } from "@/lib/shop";
import { useAuth, authHeaders } from "@/lib/auth";
import CheckoutMap from "@/components/CheckoutMap";

const BOT_USERNAME = "faxfloresbot";

const ISO_REG: Record<string, string> = {
  "UZ-TK": "Toshkent shahri", "UZ-TO": "Toshkent viloyati", "UZ-SA": "Samarqand",
  "UZ-BU": "Buxoro", "UZ-AN": "Andijon", "UZ-FA": "Farg'ona", "UZ-NG": "Namangan",
  "UZ-QA": "Qashqadaryo", "UZ-SU": "Surxondaryo", "UZ-XO": "Xorazm",
  "UZ-NW": "Navoiy", "UZ-JI": "Jizzax", "UZ-SI": "Sirdaryo", "UZ-QR": "Qoraqalpog'iston",
};

function normW(x: string) {
  return (x || "").toLowerCase().replace(/['ʼ`]/g, "");
}

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, subtotal, clear, notify } = useShop();
  const { user } = useAuth();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [region, setRegion] = useState(REGIONS[0]);
  const [city, setCity] = useState("");
  const [address, setAddress] = useState("");
  const [note, setNote] = useState("");
  const [ship, setShip] = useState<"standard" | "express">("standard");
  const [pay, setPay] = useState<"cash" | "card">("cash");
  const [promo, setPromo] = useState("");
  const [pct, setPct] = useState(0);
  const [promoMsg, setPromoMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<{ id: number; no: string; total: number; prepay: number; phone: string } | null>(null);
  const [loc, setLoc] = useState<{ lat: number; lon: number } | null>(null);
  const [locating, setLocating] = useState(false);

  const onPick = async (p: { lat: number; lon: number }) => {
    setLoc(p);
    setLocating(true);
    try {
      let a: Record<string, string> = {};
      try {
        const r = await fetch(`/api/v2/geo/reverse/?lat=${p.lat}&lon=${p.lon}`);
        const j = await r.json();
        if (j.ok) a = j;
        else throw new Error("proxy");
      } catch {
        const r = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${p.lat}&lon=${p.lon}&accept-language=uz,ru`
        );
        const j = await r.json();
        a = j.address || {};
      }
      const addr = [a.road || "", a.house_number || ""].filter(Boolean).join(", ")
        || a.suburb || a.neighbourhood || a.quarter || a.district || a.city || a.town || a.village || "";
      if (addr) setAddress(addr);
      const dist = a.suburb || a.city_district || a.district || a.neighbourhood || a.quarter || a.town || a.village || "";
      if (dist) setCity(dist);
      const iso = ISO_REG[a["ISO3166-2-lvl4"] || a.iso || ""];
      if (iso) { setRegion(iso); return; }
      const n = normW(a.state || a.county || a.city || "").replace(/[^a-z ]/g, "");
      for (const o of REGIONS) {
        const w = normW(o).split(" ")[0].replace(/[^a-z]/g, "");
        if (w && w.length > 2 && n.includes(w)) { setRegion(o); break; }
      }
    } catch {
      /* jim */
    } finally {
      setLocating(false);
    }
  };

  useEffect(() => {
    if (user) {
      if (!name) setName(user.name);
      if (!phone) setPhone("+" + user.phone);
      fetch("/api/v2/addresses/", { headers: authHeaders() })
        .then((r) => (r.ok ? r.json() : []))
        .then((list) => {
          const d = (list || []).find((a: { is_default: boolean }) => a.is_default) || list[0];
          if (d) {
            if (d.region) setRegion(d.region);
            if (!city && d.city) setCity(d.city);
            if (!address && d.address) setAddress(d.address);
            if (!note && d.note) setNote(d.note);
          }
        })
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const shipFee = ship === "express" ? EXPRESS_FEE : 0;
  const discount = useMemo(() => Math.round(subtotal * pct / 100), [subtotal, pct]);
  const total = subtotal - discount + shipFee;
  const advance = pay === "card" ? total : Math.round(total / 2);
  const rest = total - advance;

  if (cart.length === 0 && !done) {
    return (
      <div className="container-x py-16 text-center">
        <h1 className="h-serif text-4xl">Savat bo&apos;sh</h1>
        <a href="/shop" className="btn btn-primary mt-6">Gul tanlash</a>
      </div>
    );
  }

  const applyPromo = async () => {
    const code = promo.trim().toUpperCase();
    if (!code) { setPct(0); setPromoMsg(""); return; }
    setPromoMsg("Tekshirilmoqda...");
    try {
      const j = await validateCoupon(code);
      if (j.ok && j.pct) { setPct(j.pct); setPromoMsg(`✅ ${j.pct}% chegirma!`); }
      else { setPct(0); setPromoMsg("⛔ " + (j.error || "topilmadi")); }
    } catch {
      setPct(0); setPromoMsg("⛔ Tekshirib bo'lmadi");
    }
  };

  const submit = async () => {
    setErr("");
    if (name.trim().length < 2) return setErr("Ismingizni yozing");
    if (phone.replace(/\D/g, "").length < 9) return setErr("Telefonni to'g'ri kiriting");
    if (city.trim().length < 2) return setErr("Shaharni yozing");
    if (address.trim().length < 5 && !loc) return setErr("Manzilni yozing yoki xaritadan belgilang 📍");
    setBusy(true);
    try {
      const key = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));
      const r = await createOrder({
        name: name.trim(), phone: phone.trim(), region, city: city.trim(),
        address: address.trim(), note: note.trim(), ship, pay,
        lat: loc ? loc.lat : null, lon: loc ? loc.lon : null,
        promo: promo.trim().toUpperCase(), client_key: key,
        items: cart.map((i) => ({ slug: i.slug, qty: i.qty })),
      });
      clear();
      notify("Buyurtma qabul qilindi!");
      setDone({ id: r.id, no: r.no, total: parseFloat(r.total), prepay: parseFloat(r.prepay), phone: phone.trim() });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container-x py-10 max-w-[720px]">
      <div className="eyebrow">Buyurtma</div>
      <h1 className="h-serif text-4xl mt-2">Rasmiylashtirish</h1>

      {done && (
        <div className="text-center bg-white border border-beige rounded-2xl p-6 mt-6">
          <div className="text-5xl">✓</div>
          <h2 className="h-serif text-3xl mt-2">Buyurtma {done.no} qabul qilindi!</h2>
          <p className="text-stone-600 text-sm mt-1">Rahmat! Endi to&apos;lovni yakunlang.</p>
          <div className="text-left border border-beige rounded-xl p-4 mt-4 grid gap-1 text-sm max-w-[420px] mx-auto">
            <div className="flex justify-between"><span>Jami</span><b>{uzs(done.total)}</b></div>
            <div className="flex justify-between font-bold text-forest"><span>Oldindan to&apos;lov</span><b>{uzs(done.prepay)}</b></div>
            <div className="flex justify-between text-stone-500"><span>Qolgan</span><span>{uzs(done.total - done.prepay)}</span></div>
          </div>
          <div className="max-w-[420px] mx-auto mt-4">
            <h3 className="h-serif text-2xl">Keyingi qadam — 50% to&apos;lov 💳</h3>
            <p className="text-sm text-stone-600 mt-1"><b>{uzs(done.prepay)}</b> ni to&apos;lang va chekni botga yuboring.</p>
            <a className="btn btn-primary w-full mt-3" target="_blank" rel="noopener"
              href={`https://t.me/${BOT_USERNAME}?start=ord_${done.id}`}>
              ✈ Botga o&apos;tish va chek yuborish
            </a>
            <p className="text-xs text-stone-400 mt-2">⚠️ Aynan <b>{uzs(done.prepay)}</b> to&apos;lang — ko&apos;p ham, kam ham emas. Chek tekshirilgach, buyurtma adminga o&apos;tadi.</p>
            <div className="flex gap-2 mt-3">
              <a className="btn btn-outline flex-1 text-sm"
                href={`/track?id=${done.id}&phone=${encodeURIComponent(done.phone)}`}>Kuzatish →</a>
              <button className="btn btn-outline flex-1 text-sm" onClick={() => router.push("/shop")}>Xaridni davom ettirish</button>
            </div>
          </div>
        </div>
      )}
      {!done && (<>
      <div className="bg-white border border-beige rounded-2xl p-5 mt-6">
        <h3 className="font-bold mb-3">Tarkib</h3>
        {cart.map((i) => (
          <div key={i.slug} className="flex justify-between text-sm py-1.5 border-b border-ivory last:border-0">
            <span>{i.name} × {i.qty}</span><b>{uzs(i.price * i.qty)}</b>
          </div>
        ))}
        <div className="flex justify-between text-sm pt-2"><span>Mahsulotlar</span><b>{uzs(subtotal)}</b></div>
        {discount > 0 && <div className="flex justify-between text-sm text-green-700"><span>Chegirma −{pct}%</span><b>−{uzs(discount)}</b></div>}
        <div className="flex justify-between text-sm"><span>Yetkazish</span><b>{shipFee ? uzs(shipFee) : "Bepul"}</b></div>
        <div className="flex justify-between font-bold text-lg border-t border-beige mt-2 pt-2"><span>Jami</span><span>{uzs(total)}</span></div>
        <div className="flex justify-between font-bold text-forest"><span>Oldindan ({pay === "card" ? "100%" : "50%"})</span><span>{uzs(advance)}</span></div>
        <div className="flex justify-between text-sm text-stone-500"><span>Qolgan</span><span>{uzs(rest)}</span></div>
      </div>

      <div className="bg-white border border-beige rounded-2xl p-5 mt-4">
        <h3 className="font-bold mb-3">Promokod</h3>
        <div className="flex gap-2">
          <input value={promo} onChange={(e) => setPromo(e.target.value)} placeholder="KOD"
            className="flex-1 border border-beige rounded-xl px-4 py-3 text-sm outline-none focus:border-forest uppercase" />
          <button onClick={applyPromo} className="btn btn-outline !py-3">OK</button>
        </div>
        {promoMsg && <p className="text-sm mt-2">{promoMsg}</p>}
      </div>

      <div className="bg-white border border-beige rounded-2xl p-5 mt-4 grid gap-4">
        <h3 className="font-bold">Aloqa va manzil</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="field"><span>Ism *</span><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ali Valiyev" /></label>
          <label className="field"><span>Telefon *</span><input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998 ..." inputMode="tel" /></label>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="field"><span>Hudud *</span><select value={region} onChange={(e) => setRegion(e.target.value)}>{REGIONS.map((r) => <option key={r}>{r}</option>)}</select></label>
          <label className="field"><span>Shahar/Tuman *</span><input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Chilonzor" /></label>
        </div>
        <label className="field"><span>Manzil <small className="text-stone-400">— xarita belgilasangiz shart emas</small></span><input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Ko'cha, uy" /></label>
        <div>
          <span className="text-[13px] font-semibold text-[#4a4a44]">Xaritadan belgilash 📍</span>
          <div className="mt-1.5"><CheckoutMap onPick={onPick} /></div>
          <p className="text-xs text-stone-500 mt-1.5">
            {locating ? "📍 Manzil qidirilmoqda..." : loc ? `📍 ${loc.lat}, ${loc.lon} — manzil avtomatik to'ldirildi` : "Nuqtani bosing — manzil o'zi to'ladi"}
          </p>
        </div>
        <label className="field"><span>Izoh</span><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Tabriknoma, qavat..." /></label>
      </div>

      <div className="bg-white border border-beige rounded-2xl p-5 mt-4 grid gap-3">
        <h3 className="font-bold">Yetkazish</h3>
        {[["standard", "Standart", "3 soatgacha"], ["express", "Tezkor", `1 soat · +${uzs(EXPRESS_FEE)}`]].map(([v, b, s]) => (
          <label key={v} className={`flex gap-3 items-start border rounded-xl p-3.5 cursor-pointer ${ship === v ? "border-forest bg-forest/5" : "border-beige"}`}>
            <input type="radio" checked={ship === v} onChange={() => setShip(v as "standard" | "express")} className="mt-1 accent-[#233C32]" />
            <span><b className="block text-sm">{b}</b><small className="text-stone-500">{s}</small></span>
          </label>
        ))}
      </div>

      <div className="bg-white border border-beige rounded-2xl p-5 mt-4 grid gap-3">
        <h3 className="font-bold">To&apos;lov (faqat qo&apos;lda)</h3>
        <label className={`flex gap-3 items-start border rounded-xl p-3.5 cursor-pointer ${pay === "cash" ? "border-forest bg-forest/5" : "border-beige"}`}>
          <input type="radio" checked={pay === "cash"} onChange={() => setPay("cash")} className="mt-1 accent-[#233C32]" />
          <span><b className="block text-sm">Naqd — 50% oldindan, 50% yetkazishda</b><small className="text-stone-500">Kuryerga naqd</small></span>
        </label>
        <label className={`flex gap-3 items-start border rounded-xl p-3.5 cursor-pointer ${pay === "card" ? "border-forest bg-forest/5" : "border-beige"}`}>
          <input type="radio" checked={pay === "card"} onChange={() => setPay("card")} className="mt-1 accent-[#233C32]" />
          <span><b className="block text-sm">Karta — 100% oldindan</b><small className="text-stone-500">Click/Payme o'tkazma, admin tasdiqlaydi</small></span>
        </label>
      </div>

      {err && <p className="text-red-600 text-sm mt-4">⛔ {err}</p>}
      <button disabled={busy} onClick={submit} className="btn btn-primary w-full mt-4 !py-4">
        {busy ? "Yuborilmoqda..." : `Tasdiqlash · ${uzs(total)} (oldindan ${uzs(advance)})`}
      </button>
      <p className="text-xs text-stone-400 text-center mt-3">🔒 Ma&apos;lumotlar xavfsiz saqlanadi</p>
      </>)}
    </div>
  );
}
