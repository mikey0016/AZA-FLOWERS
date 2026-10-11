import Link from "next/link";
import { getCategories, getProducts } from "@/lib/api";
import ProductCard from "@/components/ProductCard";
import ShopFilters from "./filters";

export const dynamic = "force-dynamic";

export default async function Shop({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const q: Record<string, string> = {};
  for (const k of ["category", "q", "sort", "featured"]) if (sp[k]) q[k] = sp[k] as string;
  const [cats, items] = await Promise.all([
    getCategories().catch(() => []),
    getProducts(q).catch(() => []),
  ]);
  return (
    <div className="container-x py-10">
      <div className="eyebrow">Katalog</div>
      <h1 className="h-serif text-4xl mt-2">Barcha gullar</h1>
      <ShopFilters cats={cats} initial={q} />
      <p className="text-sm text-stone-500 my-3">{items.length} ta topildi</p>
      {items.length === 0 ? (
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
