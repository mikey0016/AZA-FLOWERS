"use client";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Lang = "uz" | "ru";

type Dict = {
  catalog: string; sale: string; about: string; contact: string;
  track: string; wishlist: string; cart: string; account: string;
  searchPh: string; shopNow: string; bestsellers: string;
  newArrivals: string; saleTitle: string; addToCart: string;
  added: string; allRights: string; categories: string; from: string;
  inStock: string; outOfStock: string; checkout: string; total: string;
  subtotal: string; delivery: string; advance: string; remaining: string;
  cash: string; card: string;
};

const dict: Record<Lang, Dict> = {
  uz: {
    catalog: "Katalog", sale: "Aksiya", about: "Biz haqimizda", contact: "Aloqa",
    track: "Kuzatish", wishlist: "Sevimlilar", cart: "Savat", account: "Kabinet",
    searchPh: "Gul qidirish...", shopNow: "Buketlarni ko'rish", bestsellers: "Xitlar",
    newArrivals: "Yangiliklar", saleTitle: "Chegirmalar", addToCart: "Savatga",
    added: "Savatga qo'shildi", allRights: "Barcha huquqlar himoyalangan",
    categories: "Kategoriyalar", from: "dan", inStock: "Mavjud", outOfStock: "Tugagan",
    checkout: "Buyurtma berish", total: "Jami", subtotal: "Mahsulotlar",
    delivery: "Yetkazish", advance: "Oldindan to'lov", remaining: "Qolgan",
    cash: "Naqd (50/50)", card: "Karta (100%)",
  },
  ru: {
    catalog: "Каталог", sale: "Акции", about: "О нас", contact: "Контакты",
    track: "Отследить", wishlist: "Избранное", cart: "Корзина", account: "Кабинет",
    searchPh: "Поиск цветов...", shopNow: "Смотреть букеты", bestsellers: "Хиты",
    newArrivals: "Новинки", saleTitle: "Скидки", addToCart: "В корзину",
    added: "Добавлено в корзину", allRights: "Все права защищены",
    categories: "Категории", from: "от", inStock: "В наличии", outOfStock: "Нет в наличии",
    checkout: "Оформить заказ", total: "Итого", subtotal: "Товары",
    delivery: "Доставка", advance: "Предоплата", remaining: "Остаток",
    cash: "Наличные (50/50)", card: "Карта (100%)",
  },
};

export type Strings = Dict;

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: Strings;
}

const Ctx = createContext<LangCtx>({ lang: "uz", setLang: () => {}, t: dict.uz });

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("uz");
  useEffect(() => {
    try {
      const s = localStorage.getItem("aza_lang");
      if (s === "uz" || s === "ru") setLangState(s);
    } catch { /* ignore */ }
  }, []);
  const setLang = (l: Lang) => {
    setLangState(l);
    try { localStorage.setItem("aza_lang", l); } catch { /* ignore */ }
    document.documentElement.lang = l === "uz" ? "uz" : "ru";
  };
  const value = useMemo(() => ({ lang, setLang, t: dict[lang] }), [lang]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useLang() {
  return useContext(Ctx);
}
