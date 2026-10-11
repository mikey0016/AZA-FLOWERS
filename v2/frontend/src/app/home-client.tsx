"use client";
import { useState } from "react";
import type { Product } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import ProductCard from "@/components/ProductCard";

export default function HomeClient({ hits, news, sale }: { hits: Product[]; news: Product[]; sale: Product[] }) {
  const { t } = useLang();
  const [tab, setTab] = useState("hit");
  const map: Record<string, Product[]> = { hit: hits, new: news, sale };
  return (
    <>
      <section className="container-x py-8">
        <h2 className="h-serif text-3xl text-center mb-2">{t.bestsellers}</h2>
        <div className="flex gap-6 justify-center border-b border-beige mb-6">
          {[{ id: "hit", label: t.bestsellers }, { id: "new", label: t.newArrivals }, { id: "sale", label: t.saleTitle }].map((x) => (
            <button key={x.id} onClick={() => setTab(x.id)}
              className={`py-2 text-[13px] font-semibold tracking-[0.14em] uppercase border-b-2 -mb-px ${tab === x.id ? "border-forest" : "border-transparent text-stone-400"}`}>
              {x.label}
            </button>
          ))}
        </div>
        <div key={tab} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {(map[tab] ?? []).slice(0, 8).map((p) => <ProductCard key={p.slug} p={p} />)}
        </div>
      </section>

      <section className="bg-sage/60 mt-8">
        <div className="container-x grid sm:grid-cols-3 gap-4 py-10 text-center">
          {[["🚚", "Tez yetkazish", "3 soatgacha"], ["🌿", "Yangi gullar", "Har kuni"], ["🛡️", "Kafolat", "24 soat"]].map(([i, b, s]) => (
            <div key={b} className="bg-white rounded-2xl border border-beige p-6">
              <div className="text-3xl">{i}</div>
              <b className="block mt-2 text-sm tracking-wider uppercase">{b}</b>
              <span className="text-sm text-stone-500">{s}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
