"use client";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export interface CartLine {
  slug: string;
  name: string;
  price: number;
  qty: number;
  photo: string | null;
  stock: number;
}

interface ShopCtx {
  cart: CartLine[];
  add: (p: { slug: string; name: string; price: number | string; photo?: string | null; stock?: number }, qty?: number) => void;
  setQty: (slug: string, qty: number) => void;
  remove: (slug: string) => void;
  clear: () => void;
  count: number;
  subtotal: number;
  wish: string[];
  toggleWish: (slug: string) => void;
  toast: string | null;
  notify: (m: string) => void;
}

const Ctx = createContext<ShopCtx | null>(null);

function load<T>(k: string, fb: T): T {
  try {
    const v = localStorage.getItem(k);
    return v ? (JSON.parse(v) as T) : fb;
  } catch {
    return fb;
  }
}

export function ShopProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartLine[]>([]);
  const [wish, setWish] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setCart(load("aza2_cart", []));
    setWish(load("aza2_wish", []));
    setReady(true);
  }, []);

  useEffect(() => {
    if (ready) try { localStorage.setItem("aza2_cart", JSON.stringify(cart)); } catch { /* ignore */ }
  }, [cart, ready]);
  useEffect(() => {
    if (ready) try { localStorage.setItem("aza2_wish", JSON.stringify(wish)); } catch { /* ignore */ }
  }, [wish, ready]);

  useEffect(() => {
    if (!toast) return;
    const h = setTimeout(() => setToast(null), 2400);
    return () => clearTimeout(h);
  }, [toast]);

  const value = useMemo<ShopCtx>(() => ({
    cart,
    add: (p, qty = 1) => {
      setCart((c) => {
        const f = c.find((x) => x.slug === p.slug);
        const price = typeof p.price === "string" ? parseFloat(p.price) : p.price;
        if (f) {
          return c.map((x) => x.slug === p.slug
            ? { ...x, qty: Math.min(x.stock || 50, x.qty + qty) } : x);
        }
        return [...c, { slug: p.slug, name: p.name, price, qty, photo: p.photo ?? null, stock: p.stock ?? 50 }];
      });
    },
    setQty: (slug, qty) => setCart((c) => qty <= 0
      ? c.filter((x) => x.slug !== slug)
      : c.map((x) => x.slug === slug ? { ...x, qty: Math.min(x.stock || 50, qty) } : x)),
    remove: (slug) => setCart((c) => c.filter((x) => x.slug !== slug)),
    clear: () => setCart([]),
    count: cart.reduce((a, x) => a + x.qty, 0),
    subtotal: cart.reduce((a, x) => a + x.price * x.qty, 0),
    wish,
    toggleWish: (slug) => setWish((w) => w.includes(slug) ? w.filter((x) => x !== slug) : [...w, slug]),
    toast,
    notify: (m: string) => setToast(m),
  }), [cart, wish, toast]);

  return (
    <Ctx.Provider value={value}>
      {children}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[130] bg-forest text-white px-6 py-3 rounded-full text-sm font-semibold shadow-xl">
          {toast}
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useShop(): ShopCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useShop outside provider");
  return v;
}
