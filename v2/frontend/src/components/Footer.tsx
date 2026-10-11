"use client";
import Link from "next/link";
import { useLang } from "@/lib/i18n";

export default function Footer() {
  const { t, lang } = useLang();
  return (
    <footer className="bg-forest-deep text-white mt-16">
      <div className="container-x grid sm:grid-cols-2 lg:grid-cols-4 gap-8 py-12">
        <div>
          <div className="h-serif text-2xl tracking-[0.18em]">AZA</div>
          <div className="text-[10px] tracking-[0.3em] opacity-70 font-semibold">FLOWERS</div>
          <p className="text-sm opacity-70 mt-4 leading-relaxed">
            {lang === "uz"
              ? "Toshkentdagi premium gul uyi. Har kuni yangi uzilgan gullar."
              : "Премиальный цветочный дом в Ташкенте. Свежие цветы каждый день."}
          </p>
        </div>
        <div>
          <div className="text-xs font-bold tracking-[0.2em] uppercase text-sage mb-4">
            {lang === "uz" ? "Xaridorga" : "Покупателю"}
          </div>
          <div className="grid gap-2.5 text-sm opacity-80">
            <Link href="/shop">{t.catalog}</Link>
            <Link href="/wishlist">{t.wishlist}</Link>
            <Link href="/track">{t.track}</Link>
          </div>
        </div>
        <div>
          <div className="text-xs font-bold tracking-[0.2em] uppercase text-sage mb-4">
            {lang === "uz" ? "Ma'lumot" : "Информация"}
          </div>
          <div className="grid gap-2.5 text-sm opacity-80">
            <Link href="/about">{t.about}</Link>
            <Link href="/contact">{t.contact}</Link>
            <Link href="/shop?sort=discount">{t.sale}</Link>
          </div>
        </div>
        <div>
          <div className="text-xs font-bold tracking-[0.2em] uppercase text-sage mb-4">
            {lang === "uz" ? "To'lov" : "Оплата"}
          </div>
          <div className="flex gap-2 flex-wrap">
            {["CLICK", "PAYME", "UZCARD", "HUMO", "VISA"].map((p) => (
              <span key={p} className="border border-white/30 rounded px-2.5 py-1 text-[11px] tracking-widest">{p}</span>
            ))}
          </div>
          <div className="text-sm opacity-70 mt-4">+998 90 350 71 78</div>
        </div>
      </div>
      <div className="border-t border-white/15">
        <div className="container-x py-4 flex flex-wrap gap-2 justify-between text-xs opacity-60">
          <span>© 2026 AZA FLOWERS. {t.allRights}.</span>
          <span>08:00 – 22:00</span>
        </div>
      </div>
    </footer>
  );
}
