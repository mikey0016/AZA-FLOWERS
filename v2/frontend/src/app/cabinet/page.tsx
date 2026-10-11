"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, authHeaders } from "@/lib/auth";
import type { Order } from "@/lib/api";
import { uzs } from "@/lib/format";

interface Addr {
  id: number;
  label: string;
  region: string;
  city: string;
  address: string;
  note: string;
  is_default: boolean;
}

async function api(path: string, init?: RequestInit) {
  const r = await fetch(path, { cache: "no-store", ...init });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}

export default function CabinetPage() {
  const router = useRouter();
  const { user, token, logout } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [addrs, setAddrs] = useState<Addr[]>([]);
  const [showAddr, setShowAddr] = useState(false);
  const [form, setForm] = useState({ label: "Uy", region: "", city: "", address: "", note: "" });

  useEffect(() => {
    if (token === null) return;
    if (!token) { router.replace("/login"); return; }
    const h = authHeaders();
    api("/api/v2/my/orders/", { headers: h }).then(setOrders).catch(() => {});
    api("/api/v2/addresses/", { headers: h }).then((j: Addr[]) => setAddrs(j)).catch(() => {});
  }, [token, router]);

  if (!user) return <div className="container-x py-16 text-center text-stone-400">Yuklanmoqda...</div>;

  const saveAddr = async () => {
    if (form.city.trim().length < 2 || form.address.trim().length < 5) return;
    await api("/api/v2/addresses/", {
      method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ ...form, is_default: addrs.length === 0 }),
    });
    const j: Addr[] = await api("/api/v2/addresses/", { headers: authHeaders() });
    setAddrs(j);
    setShowAddr(false);
    setForm({ label: "Uy", region: "", city: "", address: "", note: "" });
  };

  const delAddr = async (id: number) => {
    await api(`/api/v2/addresses/${id}/`, { method: "DELETE", headers: authHeaders() }).catch(() => {});
    setAddrs((a) => a.filter((x) => x.id !== id));
  };

  return (
    <div className="container-x py-10 max-w-[760px]">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="eyebrow">Kabinet</div>
          <h1 className="h-serif text-4xl mt-1">{user.name}</h1>
          <p className="text-sm text-stone-500">{user.phone}</p>
        </div>
        <button onClick={() => { logout(); router.push("/"); }} className="btn btn-outline !py-2.5 text-sm">Chiqish</button>
      </div>

      <h2 className="font-bold mt-8 mb-3">Manzillarim</h2>
      {addrs.map((a) => (
        <div key={a.id} className="bg-white border border-beige rounded-xl p-4 mb-2 flex justify-between gap-2">
          <div className="text-sm">
            <b>{a.label}</b> {a.is_default && <span className="text-xs bg-sage rounded-full px-2 py-0.5">asosiy</span>}
            <div className="text-stone-500">{[a.region, a.city, a.address].filter(Boolean).join(", ")}</div>
          </div>
          <button onClick={() => delAddr(a.id)} className="text-stone-400 hover:text-red-600">✕</button>
        </div>
      ))}
      {!showAddr
        ? <button onClick={() => setShowAddr(true)} className="btn btn-outline !py-2.5 text-sm mt-1">+ Manzil qo&apos;shish</button>
        : (
          <div className="bg-white border border-beige rounded-xl p-4 grid gap-2 mt-2">
            <div className="grid sm:grid-cols-2 gap-2">
              <label className="field"><span>Nom</span><input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} /></label>
              <label className="field"><span>Hudud</span><input value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} /></label>
            </div>
            <label className="field"><span>Shahar *</span><input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></label>
            <label className="field"><span>Manzil *</span><input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>
            <button onClick={saveAddr} className="btn btn-primary">Saqlash</button>
          </div>
        )}

      <h2 className="font-bold mt-8 mb-3">Buyurtmalarim</h2>
      {orders.length === 0 && <p className="text-stone-400 text-sm">Hali buyurtma yo&apos;q. <Link href="/shop" className="text-forest font-semibold">Gul tanlash →</Link></p>}
      {orders.map((o) => (
        <Link key={o.id} href={`/track?id=${o.id}&phone=${user.phone}`} className="block bg-white border border-beige rounded-xl p-4 mb-2 hover:border-forest">
          <div className="flex justify-between text-sm">
            <b>{o.no}</b>
            <span className="text-xs bg-sage rounded-full px-2 py-0.5">{o.status}</span>
          </div>
          <div className="text-xs text-stone-500 mt-1">{o.created_at} • {(o.items || []).map((l) => `${l.name} × ${l.qty}`).join(", ")}</div>
          <div className="font-bold mt-1">{uzs(o.total)}</div>
        </Link>
      ))}
    </div>
  );
}
