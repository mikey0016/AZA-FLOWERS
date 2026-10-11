import Link from "next/link";
import { notFound } from "next/navigation";
import { getProduct, getProducts } from "@/lib/api";
import { uzs } from "@/lib/format";
import FlowerArt from "@/components/FlowerArt";
import BuyBox from "./buy-box";
import ProductCard from "@/components/ProductCard";

export async function generateStaticParams() {
  try {
    const items = await getProducts({});
    return items.map((p) => ({ slug: p.slug }));
  } catch {
    return [];
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const p = await getProduct(slug);
    return { title: `${p.name_uz} — FAX Flores`, description: p.description_uz.slice(0, 150) };
  } catch {
    return { title: "Mahsulot — FAX Flores" };
  }
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let p;
  try {
    p = await getProduct(slug);
  } catch {
    notFound();
  }
  const related = await getProducts({ category: p.category.slug }).catch(() => []);
  return (
    <div className="container-x py-8">
      <p className="text-[13px] text-stone-500 mb-4">
        <Link href="/">Bosh sahifa</Link> / <Link href="/shop">Katalog</Link> /{" "}
        <Link href={`/shop?category=${p.category.slug}`}>{p.category.name_uz}</Link> / {p.name_uz}
      </p>
      <div className="grid md:grid-cols-2 gap-8 bg-white border border-beige rounded-3xl p-4 sm:p-6">
        <div className="rounded-2xl overflow-hidden bg-ivory aspect-square">
          {p.photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.photo} alt={p.name_uz} className="w-full h-full object-cover" />
          ) : (
            <FlowerArt seed={p.id} className="w-full h-full" />
          )}
        </div>
        <div>
          <div className="text-xs font-bold tracking-[0.18em] uppercase text-forest/70">{p.category.name_uz}</div>
          <h1 className="h-serif text-3xl sm:text-4xl mt-2">{p.name_uz}</h1>
          <div className="text-amber-500 text-sm tracking-[0.2em] mt-2">★★★★★ <span className="text-stone-400">4.9</span></div>
          <p className="text-stone-600 leading-relaxed mt-4">{p.description_uz}</p>
          <div className="flex items-baseline gap-3 mt-4">
            <span className="text-3xl font-semibold">{uzs(p.price)}</span>
            {p.old_price && <span className="text-stone-400 line-through">{uzs(p.old_price)}</span>}
          </div>
          <div className="text-sm mt-1 text-stone-500">
            {p.stock > 0 ? `● Mavjud: ${p.stock} dona` : "○ Tugagan"}
          </div>
          <BuyBox p={{ slug: p.slug, name: p.name_uz, price: p.price, photo: p.photo, stock: p.stock }} />
          <div className="mt-5 text-sm text-stone-500 bg-ivory border border-beige rounded-xl p-4 leading-relaxed">
            🚚 Toshkent bo&apos;ylab 3 soatgacha yetkazish
            <br />📸 Jo&apos;natishdan oldin foto yuboramiz
            <br />💳 Naqd 50/50 yoki karta 100%
          </div>
        </div>
      </div>
      {related.filter((x) => x.slug !== p.slug).length > 0 && (
        <>
          <h2 className="h-serif text-3xl mt-12 mb-4">Tavsiya etamiz</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {related.filter((x) => x.slug !== p.slug).slice(0, 4).map((x) => <ProductCard key={x.slug} p={x} />)}
          </div>
        </>
      )}
    </div>
  );
}
