"use client";
import { useRouter, useSearchParams } from "next/navigation";
import type { Category } from "@/lib/api";

export default function ShopFilters({ cats, initial }: { cats: Category[]; initial: Record<string, string> }) {
  const router = useRouter();
  const sp = useSearchParams();
  const go = (patch: Record<string, string>) => {
    const q = new URLSearchParams(sp.toString());
    for (const [k, v] of Object.entries(patch)) {
      if (v) q.set(k, v); else q.delete(k);
    }
    router.push("/shop" + (q.toString() ? "?" + q.toString() : ""));
  };
  const cur = initial.category || "all";
  return (
    <>
      <div className="flex gap-2 flex-wrap my-4">
        {[{ slug: "all", name_uz: "Barchasi", name_ru: "", id: 0 }, ...cats].map((c) => (
          <button key={c.slug}
            onClick={() => go({ category: c.slug === "all" ? "" : c.slug })}
            className={`border rounded-full px-5 py-2 text-[13px] font-semibold ${cur === c.slug ? "bg-forest text-white border-forest" : "bg-white border-beige hover:border-forest"}`}>
            {c.name_uz}
          </button>
        ))}
      </div>
      <div className="flex gap-2 flex-wrap items-center">
        <input defaultValue={initial.q || ""} placeholder="Qidiruv..."
          onKeyDown={(e) => { if (e.key === "Enter") go({ q: (e.target as HTMLInputElement).value }); }}
          className="border border-beige rounded-full px-5 py-2.5 text-sm bg-white outline-none focus:border-forest flex-1 min-w-[200px]" />
        <select defaultValue={initial.sort || "popular"} onChange={(e) => go({ sort: e.target.value })}
          className="border border-beige rounded-full px-4 py-2.5 text-sm bg-white">
          <option value="popular">Mashhur</option>
          <option value="cheap">Arzon</option>
          <option value="expensive">Qimmat</option>
          <option value="new">Yangi</option>
          <option value="discount">Chegirma</option>
        </select>
      </div>
    </>
  );
}
