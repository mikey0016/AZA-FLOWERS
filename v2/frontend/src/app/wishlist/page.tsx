"use client";
import Link from "next/link";
import { useShop } from "@/lib/shop";
import { useLang } from "@/lib/i18n";
import ProductCard from "@/components/ProductCard";
import { useEffect, useState } from "react";
import { getProducts, type Product } from "@/lib/api";

export default function WishlistPage() {
  const { wish } = useShop();
  const { t } = useLang();
  const [items, setItems] = useState<Product[]>([]);
  useEffect(() => {
    if (!wish.length) { setItems([]); return; }
    getProducts({}).then((all) => setItems(all.filter((p) => wish.includes(p.slug)))).catch(() => {});
  }, [wish]);
  return (
    <div className="container-x py-10">
      <div className="eyebrow">{t.wishlist}</div>
      <h1 className="h-serif text-4xl mt-2">Saqlangan gullar</h1>
      {items.length === 0 ? (
        <div className="text-center py-16 text-stone-400">
          Sevimlilar bo&apos;sh
          <div><Link href="/shop" className="btn btn-primary mt-4">{t.catalog} →</Link></div>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {items.map((p) => <ProductCard key={p.slug} p={p} />)}
        </div>
      )}
    </div>
  );
}
