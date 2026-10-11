import Link from "next/link";
import { getCategories, getProducts } from "@/lib/api";
import ProductCard from "@/components/ProductCard";
import HomeClient from "./home-client";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [cats, hits, news, sale] = await Promise.all([
    getCategories().catch(() => []),
    getProducts({ sort: "popular" }).catch(() => []),
    getProducts({ sort: "new" }).catch(() => []),
    getProducts({ sort: "discount" }).catch(() => []),
  ]);
  return (
    <div>
      {/* HERO */}
      <section className="bg-forest text-white overflow-hidden">
        <div className="container-x grid lg:grid-cols-2 gap-10 items-center py-14 lg:py-20">
          <div>
            <div className="eyebrow !text-sage">Premium gul uyi — Toshkent</div>
            <h1 className="h-serif text-4xl sm:text-5xl lg:text-[56px] mt-4">
              Sevgingizni gullar bilan ayting
            </h1>
            <p className="mt-4 text-white/75 max-w-[52ch] leading-relaxed">
              101 dona atirguldan to&apos;y buketigacha — har bir gul qo&apos;lda saralangan.
              Jo&apos;natishdan oldin foto yuboramiz, 3 soatgacha yetkazamiz.
            </p>
            <div className="flex flex-wrap gap-3 mt-7">
              <Link href="/shop" className="btn bg-white text-forest px-8 py-4 text-sm hover:bg-sage">
                Buketlarni ko&apos;rish
              </Link>
              <Link href="/shop?sort=discount" className="btn border-[1.5px] border-white/60 text-white px-8 py-4 text-sm hover:bg-white hover:text-forest">
                Aksiya −20%
              </Link>
            </div>
            <div className="flex gap-6 mt-8 text-sm">
              <div><b className="h-serif text-2xl block">14+</b><span className="opacity-70">mahsulot</span></div>
              <div><b className="h-serif text-2xl block">4.9 ★</b><span className="opacity-70">baho</span></div>
              <div><b className="h-serif text-2xl block">3 soat</b><span className="opacity-70">yetkazish</span></div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {hits.slice(0, 4).map((p, i) => (
              <Link key={p.slug} href={`/product/${p.slug}`}
                className={`bg-white/10 backdrop-blur rounded-2xl p-3 hover:bg-white/15 transition ${i % 2 ? "mt-6" : ""}`}>
                <div className="font-semibold text-sm truncate">{p.name_uz}</div>
                <div className="text-sage text-sm">{Number(p.price).toLocaleString("uz-UZ")} so&apos;m</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="container-x py-12">
        <h2 className="h-serif text-3xl text-center">Kategoriyalar</h2>
        <div className="flex gap-4 justify-start sm:justify-center overflow-x-auto py-6">
          {cats.map((c) => (
            <Link key={c.slug} href={`/shop?category=${c.slug}`} className="flex-none w-[130px] text-center group">
              <div className="w-[96px] h-[96px] mx-auto rounded-full bg-sage grid place-items-center text-4xl group-hover:scale-105 transition border border-beige">
                🌸
              </div>
              <b className="block mt-2 text-sm font-semibold">{c.name_uz}</b>
            </Link>
          ))}
        </div>
      </section>

      <HomeClient hits={hits} news={news} sale={sale} />
    </div>
  );
}
