"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { trackOrder, uploadReceipt, type Order } from "@/lib/api";
import { uzs } from "@/lib/format";

const ST_UZ: Record<string, string> = {
  new: "Yangi", awaiting_payment: "To'lov kutilmoqda", awaiting_verify: "Tekshiruvda",
  confirmed: "Tasdiqlangan", preparing: "Tayyorlanmoqda", ready: "Tayyor",
  delivering: "Yo'lda", delivered: "Yetkazildi", cancelled: "Bekor qilingan",
};

export default function TrackPage() {
  return (
    <Suspense fallback={<div className="container-x py-16 text-center text-stone-400">Yuklanmoqda...</div>}>
      <TrackInner />
    </Suspense>
  );
}

function TrackInner() {
  const sp = useSearchParams();
  const [id, setId] = useState(sp.get("id") || "");
  const [phone, setPhone] = useState(sp.get("phone") || "");
  const [order, setOrder] = useState<Order | null>(null);
  const [err, setErr] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [ref, setRef] = useState("");
  const [upMsg, setUpMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async (oid: string, ph: string) => {
    setErr("");
    try {
      setOrder(await trackOrder(oid, ph));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Topilmadi");
      setOrder(null);
    }
  };

  useEffect(() => {
    if (sp.get("id") && sp.get("phone")) load(sp.get("id")!, sp.get("phone")!);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!order || !id || !phone) return;
    if (["delivered", "cancelled"].includes(order.status)) return;
    const h = setInterval(() => trackOrder(id, phone).then(setOrder).catch(() => {}), 15000);
    return () => clearInterval(h);
  }, [order, id, phone]);

  const sendReceipt = async () => {
    if (!file || !order?.payment) return;
    setBusy(true);
    setUpMsg("");
    try {
      const fd = new FormData();
      fd.append("payment_id", String(order.payment.id));
      fd.append("phone", phone);
      fd.append("reference", ref);
      fd.append("file", file);
      const j = await uploadReceipt(fd);
      if (!j.ok) throw new Error(j.error || "Xatolik");
      setUpMsg("✅ Chek yuborildi! Admin tekshirmoqda.");
      setFile(null);
      load(String(order.id), phone);
    } catch (e) {
      setUpMsg("⛔ " + (e instanceof Error ? e.message : "Xatolik"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container-x py-10 max-w-[680px]">
      <div className="eyebrow">Kuzatish</div>
      <h1 className="h-serif text-4xl mt-2">Buyurtmani kuzatish</h1>
      <div className="bg-white border border-beige rounded-2xl p-5 mt-6 grid gap-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="field"><span>Raqam *</span><input value={id} onChange={(e) => setId(e.target.value)} placeholder="Buyurtma ID" inputMode="numeric" /></label>
          <label className="field"><span>Telefon *</span><input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998 ..." inputMode="tel" /></label>
        </div>
        <button onClick={() => load(id, phone)} className="btn btn-primary w-full">Topish →</button>
        {err && <p className="text-red-600 text-sm">⛔ {err}</p>}
      </div>

      {order && <OrderView order={order} />}

      {order?.payment && (
        <div className="bg-white border border-beige rounded-2xl p-5 mt-4">
          <h3 className="font-bold mb-3">To&apos;lov — {order.pay_method === "card" ? "Karta (100%)" : "Naqd (50/50)"}</h3>
          <Row k="Jami" v={uzs(order.total)} />
          <Row k="Talab qilinadi" v={uzs(order.payment.required_amount)} strong />
          <Row k="Qabul qilindi" v={uzs(order.payment.received)} />
          <Row k="Qolgan" v={uzs(order.payment.remaining)} />
          <Row k="Holat" v={order.payment.status} />
          {order.pay_method === "card" && order.payment.card_number && (
            <div className="mt-3 text-sm bg-ivory border border-beige rounded-xl p-4">
              💳 <b>{order.payment.cardholder}</b><br />
              <code className="text-lg tracking-wider">{order.payment.card_number}</code>
              {order.payment.instructions && <p className="mt-1 text-stone-500">{order.payment.instructions}</p>}
              <p className="mt-1 text-stone-500">Aynan {uzs(order.payment.required_amount)} o&apos;tkazing, chekni pastga yuklang.</p>
            </div>
          )}
          <div className="mt-4 grid gap-2">
            <h4 className="font-semibold text-sm">Chek yuklash (JPG/PNG/WEBP/PDF, 8MB)</h4>
            <input type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="text-sm" />
            <input value={ref} onChange={(e) => setRef(e.target.value)} placeholder="Tranzaksiya raqami (ixtiyoriy)"
              className="border border-beige rounded-xl px-4 py-2.5 text-sm" />
            <button disabled={busy || !file} onClick={sendReceipt} className="btn btn-primary disabled:opacity-40">
              {busy ? "Yuklanmoqda..." : "📸 Chekni yuborish"}
            </button>
            {upMsg && <p className="text-sm">{upMsg}</p>}
            <p className="text-xs text-stone-400">Chek yuklash to&apos;lovni avtomatik tasdiqlamaydi — admin tekshiradi.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <div className="flex justify-between text-sm py-1">
      <span className="text-stone-500">{k}</span>
      <b className={strong ? "text-forest" : ""}>{v}</b>
    </div>
  );
}

function OrderView({ order }: { order: Order }) {
  return (
    <div className="bg-white border border-beige rounded-2xl p-5 mt-4">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <b className="text-lg">{order.no}</b>
        <span className="text-xs font-bold bg-sage rounded-full px-3 py-1">{ST_UZ[order.status] || order.status}</span>
      </div>
      <div className="text-sm text-stone-500 mt-1">{order.created_at} • {order.city}, {order.address}</div>
      <div className="mt-3 grid gap-1.5 text-sm">
        {order.items.map((i, n) => (
          <div key={n} className="flex justify-between"><span>{i.name} × {i.qty}</span><b>{uzs(i.line_total)}</b></div>
        ))}
      </div>
      <div className="flex justify-between font-bold border-t border-beige mt-2 pt-2"><span>Jami</span><span>{uzs(order.total)}</span></div>
      {order.history.length > 0 && (
        <div className="mt-3 text-xs text-stone-500">
          {order.history.map((h, n) => <div key={n}>→ {h.to} <span className="opacity-60">({h.by || "tizim"})</span></div>)}
        </div>
      )}
    </div>
  );
}
