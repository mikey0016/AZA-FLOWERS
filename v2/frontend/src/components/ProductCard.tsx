"use client";
import Link from "next/link";
import type { Product } from "@/lib/api";
import { uzs } from "@/lib/format";
import { useLang } from "@/lib/i18n";
import { useShop } from "@/lib/shop";
import FlowerArt from "./FlowerArt";

export default function ProductCard({ p }: { p: Product }) {
  const { t, lang } = useLang();
  const { add, wish, toggleWish, notify } = useShop();
  const name = lang === "ru" && p.name_ru ? p.name_ru : p.name_uz;
  const price = parseFloat(p.price);
  const liked = wish.includes(p.slug);
  return (
    <div className="card group">
      <div className="relative bg-ivory aspect-square overflow-hidden">
        <Link href={`/product/${p.slug}`} className="block w-full h-full">
          {p.photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.photo} alt={name} loading="lazy" className="w-full h-full object-cover transition duration-500 group-hover:scale-105" />
          ) : (
            <FlowerArt seed={p.id} className="w-full h-full transition duration-500 group-hover:scale-105" />
          )}
        </Link>
        <div className="absolute top-3 left-3 flex gap-1.5">
          {p.discount_pct > 0 && (
            <span className="text-[11px] font-bold bg-red-500 text-white rounded px-2 py-1">-{p.discount_pct}%</span>
          )}
          {p.featured === 1 && (
            <span className="text-[11px] font-bold bg-charcoal text-white rounded px-2 py-1">TOP</span>
          )}
          {p.featured === 2 && (
            <span className="text-[11px] font-bold bg-forest text-white rounded px-2 py-1">NEW</span>
          )}
        </div>
        <button
          aria-label="wishlist"
          onClick={() => toggleWish(p.slug)}
          className={`absolute top-3 right-3 w-9 h-9 rounded-full grid place-items-center border transition text-lg ${liked ? "bg-red-500 border-red-500 text-white" : "bg-white/90 border-beige hover:border-forest"}`}
        >
          {liked ? "♥" : "♡"}
        </button>
        <button
          disabled={p.stock <= 0}
          onClick={() => { add({ slug: p.slug, name, price, photo: p.photo, stock: p.stock }); notify("✓ " + t.added); }}
          className="absolute inset-x-0 bottom-0 bg-charcoal/90 text-white text-xs font-semibold tracking-[0.14em] uppercase py-3 translate-y-full group-hover:translate-y-0 transition max-sm:translate-y-0 max-sm:static max-sm:mt-2 max-sm:mx-3 max-sm:rounded-full max-sm:mb-3 disabled:opacity-40"
        >
          {p.stock > 0 ? t.addToCart : t.outOfStock}
        </button>
      </div>
      <div className="p-4 flex flex-col gap-1.5">
        <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-forest/70">{p.category.name_uz}</div>
        <Link href={`/product/${p.slug}`} className="h-serif text-xl leading-snug hover:text-forest">{name}</Link>
        <div className="text-amber-500 text-xs tracking-[0.2em]">★★★★★ <span className="text-stone-400 tracking-normal">4.9</span></div>
        <div className="flex items-baseline gap-2">
          <span className="font-semibold text-lg">{uzs(price)}</span>
          {p.old_price && <span className="text-stone-400 line-through text-sm">{uzs(p.old_price)}</span>}
        </div>
        <div className="text-xs text-stone-500">{p.stock > 0 ? `● ${t.inStock}` : `○ ${t.outOfStock}`}</div>
      </div>
    </div>
  );
}
