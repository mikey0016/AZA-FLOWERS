"use client";
import Link from "next/link";
import { useState } from "react";
import { useLang, type Lang } from "@/lib/i18n";
import { useShop } from "@/lib/shop";
import { useAuth } from "@/lib/auth";

const NAV = [
  { uz: "Katalog", ru: "Каталог", href: "/shop" },
  { uz: "Aksiya", ru: "Акции", href: "/shop?sort=discount" },
  { uz: "Biz haqimizda", ru: "О нас", href: "/about" },
  { uz: "Aloqa", ru: "Контакты", href: "/contact" },
  { uz: "Kuzatish", ru: "Отследить", href: "/track" },
];

export default function Header() {
  const { t, lang, setLang } = useLang();
  const { count, wish } = useShop();
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState(false);

  const flip = (l: Lang) => setLang(l);

  return (
    <header className="sticky top-0 z-[60] bg-ivory/95 backdrop-blur border-b border-beige">
      <div className="bg-forest text-white text-xs">
        <div className="container-x flex items-center gap-4 py-2">
          <span className="flex gap-1">
            <button onClick={() => flip("uz")} className={lang === "uz" ? "font-bold underline" : "opacity-70"}>UZ</button>
            <span className="opacity-50">|</span>
            <button onClick={() => flip("ru")} className={lang === "ru" ? "font-bold underline" : "opacity-70"}>RU</button>
          </span>
          <span className="hidden sm:inline opacity-90">+998 90 350 71 78</span>
          <span className="flex-1" />
          <span className="opacity-90 hidden md:inline">{lang === "uz" ? "Har hafta yangi gullar!" : "Новые цветы каждую неделю!"}</span>
        </div>
      </div>
      <div className="container-x flex items-center gap-4 py-3">
        <button className="lg:hidden text-2xl" aria-label="menu" onClick={() => setOpen(true)}>☰</button>
        <Link href="/" className="leading-none">
          <span className="h-serif text-[26px] font-semibold tracking-[0.18em] text-forest">FAX</span>
          <span className="block text-[9px] tracking-[0.3em] text-stone-500 font-semibold">FLOWERS</span>
        </Link>
        <nav className="hidden lg:flex gap-6 mx-auto">
          {NAV.map((n) => (
            <Link key={n.href + n.uz} href={n.href} className="text-[13px] font-semibold tracking-[0.1em] uppercase text-charcoal/80 hover:text-forest">
              {lang === "uz" ? n.uz : n.ru}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-1 ml-auto lg:ml-0">
          <Link href={user ? "/cabinet" : "/login"} title={t.account}
            className="w-10 h-10 grid place-items-center text-lg hover:text-forest font-semibold">
            {user ? user.name.trim()[0].toUpperCase() : "👤"}
          </Link>
          <button aria-label="search" className="w-10 h-10 grid place-items-center text-xl hover:text-forest" onClick={() => setSearch((s) => !s)}>⌕</button>
          <Link aria-label="wishlist" href="/wishlist" className="relative w-10 h-10 grid place-items-center text-xl hover:text-forest">
            ♡
            {wish.length > 0 && (
              <span className="absolute top-0 right-0 min-w-[18px] h-[18px] rounded-full bg-forest text-white text-[10px] font-bold grid place-items-center px-1">{wish.length}</span>
            )}
          </Link>
          <Link aria-label="cart" href="/checkout" className="relative w-10 h-10 grid place-items-center text-xl hover:text-forest">
            🛒
            <span className="absolute top-0 right-0 min-w-[18px] h-[18px] rounded-full bg-forest text-white text-[10px] font-bold grid place-items-center px-1">{count}</span>
          </Link>
        </div>
      </div>
      {search && (
        <div className="border-t border-beige bg-white">
          <form
          className="container-x py-3 flex gap-2"
            onSubmit={(e) => { e.preventDefault(); location.href = "/shop?q=" + encodeURIComponent(q); }}
          >
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.searchPh}
              className="flex-1 border border-beige rounded-full px-5 py-2.5 text-sm outline-none focus:border-forest" />
            <button className="btn btn-primary !py-2.5 !px-6 text-sm">→</button>
          </form>
        </div>
      )}
      {open && (
        <div className="fixed inset-0 z-[120]">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-[300px] bg-ivory p-6 flex flex-col gap-1 shadow-2xl">
            <button className="self-end text-2xl" onClick={() => setOpen(false)}>✕</button>
            <Link href="/" onClick={() => setOpen(false)} className="py-3 border-b border-beige font-semibold">FAX Flores</Link>
            {NAV.map((n) => (
              <Link key={n.href + n.uz} href={n.href} onClick={() => setOpen(false)}
                className="py-3 border-b border-beige text-sm font-semibold tracking-wider uppercase">
                {lang === "uz" ? n.uz : n.ru}
              </Link>
            ))}
          </aside>
        </div>
      )}
    </header>
  );
}
