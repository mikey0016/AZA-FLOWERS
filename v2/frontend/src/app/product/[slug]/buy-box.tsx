"use client";
import { useState } from "react";
import Link from "next/link";
import { useShop } from "@/lib/shop";

export default function BuyBox({ p }: { p: { slug: string; name: string; price: number | string; photo: string | null; stock: number } }) {
  const { add, toggleWish, wish } = useShop();
  const [qty, setQty] = useState(1);
  const liked = wish.includes(p.slug);
  return (
    <div className="mt-5 grid gap-2">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 border border-beige rounded-full px-2 py-1">
          <button className="w-8 h-8 text-lg" onClick={() => setQty((q) => Math.max(1, q - 1))}>−</button>
          <b className="w-6 text-center">{qty}</b>
          <button className="w-8 h-8 text-lg" onClick={() => setQty((q) => Math.min(20, q + 1))}>+</button>
        </div>
        <span className="text-xs text-stone-400">Omborda: {p.stock}</span>
      </div>
      <button disabled={p.stock <= 0} onClick={() => add(p, qty)} className="btn btn-primary w-full disabled:opacity-40">
        Savatga qo&apos;shish
      </button>
      <div className="flex gap-2">
        <button onClick={() => toggleWish(p.slug)} className="btn btn-outline flex-1">
          {liked ? "♥ Sevimlida" : "♡ Sevimlilarga"}
        </button>
        <Link href="/checkout" onClick={() => add(p, qty)} className="btn btn-outline flex-1 text-center">
          Hozir olish →
        </Link>
      </div>
    </div>
  );
}
