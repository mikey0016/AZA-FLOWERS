"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { getCategories, getProducts, type Category, type Product } from "@/lib/api";
import ProductCard from "@/components/ProductCard";

function ShopInner() {
  const sp = useSearchParams();
  const router = useRouter();
  const [cats, setCats] = useState<Category[]>([]);
  const [items, setItems] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState(sp.get("sort") || "popular");
  const [q, setQ] = useState(sp.get("q") || "");
  const cat = sp.get("category") || "all";

  useEffect(() => {
    getCategories().then(setCats).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const p: Record<string, string> = {};
    if (cat !== "all") p.category = cat;
    if (q) p.q = q;
    if (sort) p.sort = sort;
    getProducts(p).then((v) => { setItems(v); setLoading(false); }).catch(() => setLoading(false));
  }, [cat, q, sort]);

  const go = (patch: Record<string, string>) => {
    const nq = new URLSearchParams(sp.toString());
    for (const [k, v] of Object.entries(patch)) {
      if (v) nq.set(k, v); else nq.delete(k);
    }
    router.push("/shop" + (nq.toString() ? "?" + nq.toString() : ""));
  };

  return (
    <div className="container-x py-10">
      <div className="eyebrow">Katalog</div>
      <h1 className="h-serif text-4xl mt-2">Barcha gullar</h1>
      <div className="flex gap-2 flex-wrap my-4">
        {[{ slug: "all", name_uz: "Barchasi" } as Category, ...cats].map((c) => (
          <button key={c.slug}
            onClick={() => go({ category: c.slug === "all" ? "" : c.slug })}
            className={`border rounded-full px-5 py-2 text-[13px] font-semibold ${cat === c.slug ? "bg-forest text-white border-forest" : "bg-white border-beige hover:border-forest"}`}>
            {c.name_uz}
          </button>
        ))}
      </div>
      <div className="flex gap-2 flex-wrap items-center">
        <input defaultValue={q} placeholder="Qidiruv..."
          onKeyDown={(e) => { if (e.key === "Enter") { setQ((e.target as HTMLInputElement).value); go({ q: (e.target as HTMLInputElement).value }); } }}
          className="border border-beige rounded-full px-5 py-2.5 text-sm bg-white outline-none focus:border-forest flex-1 min-w-[200px]" />
        <select value={sort} onChange={(e) => { setSort(e.target.value); go({ sort: e.target.value }); }}
          className="border border-beige rounded-full px-4 py-2.5 text-sm bg-white">
          <option value="popular">Mashhur</option>
          <option value="cheap">Arzon</option>
          <option value="expensive">Qimmat</option>
          <option value="new">Yangi</option>
          <option value="discount">Chegirma</option>
        </select>
      </div>
      <p className="text-sm text-stone-500 my-3">{loading ? "Yuklanmoqda..." : `${items.length} ta topildi`}</p>
      {!loading && items.length === 0 ? (
        <div className="text-center py-16 text-stone-400">
          Hech narsa topilmadi
          <div><Link href="/shop" className="btn btn-outline mt-4">Filtrni tozalash</Link></div>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {items.map((p) => <ProductCard key={p.slug} p={p} />)}
        </div>
      )}
    </div>
  );
}

export default function Shop() {
  return (
    <Suspense fallback={<div className="container-x py-16 text-center text-stone-400">Yuklanmoqda...</div>}>
      <ShopInner />
    </Suspense>
  );
}
