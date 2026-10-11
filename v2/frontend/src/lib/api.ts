function apiBase(): string {
  if (typeof window !== "undefined") return "";
  return process.env.API_URL || "http://127.0.0.1:8000";
}

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(apiBase() + path, { cache: "no-store", ...init });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((data as { error?: string }).error || `HTTP ${r.status}`);
  return data as T;
}

export interface Category {
  id: number;
  slug: string;
  name_uz: string;
  name_ru: string;
}

export interface Product {
  id: number;
  slug: string;
  name_uz: string;
  name_ru: string;
  category: Category;
  price: string;
  old_price: string | null;
  discount_pct: number;
  stock: number;
  active: boolean;
  featured: number;
  description_uz: string;
  photo: string | null;
}

export interface OrderItem {
  product_slug: string;
  name: string;
  price: string;
  qty: number;
  line_total: string;
}

export interface PaymentInfo {
  id: number;
  method: string;
  required_amount: string;
  received: string;
  remaining: string;
  status: string;
  cardholder?: string;
  card_number?: string;
  instructions?: string;
}

export interface Order {
  id: number;
  no: string;
  name: string;
  phone: string;
  region: string;
  city: string;
  address: string;
  note: string;
  ship_method: string;
  ship_fee: string;
  pay_method: string;
  subtotal: string;
  discount: string;
  total: string;
  status: string;
  items: OrderItem[];
  history: { from: string; to: string; by: string; at: string }[];
  remaining: string;
  payment: PaymentInfo | null;
  created_at: string;
}

export const getCategories = () => j<Category[]>("/api/v2/shop/categories/");

export const getProducts = (p: Record<string, string> = {}) => {
  const q = new URLSearchParams(p).toString();
  return j<Product[]>(`/api/v2/shop/products/${q ? "?" + q : ""}`);
};

export const getProduct = (slug: string) => j<Product>(`/api/v2/shop/products/${slug}/`);

export interface CreateOrderBody {
  name: string;
  phone: string;
  region?: string;
  city?: string;
  address?: string;
  note?: string;
  lat?: number | null;
  lon?: number | null;
  ship?: string;
  pay?: string;
  promo?: string;
  client_key?: string;
  items: { slug: string; qty: number }[];
}

export const createOrder = (body: CreateOrderBody) =>
  j<{ ok: boolean; id: number; no: string; total: string; prepay: string; status: string; payment_id: number; pay_method: string }>(
    "/api/v2/orders/",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
  );

export const trackOrder = (id: string, phone: string) =>
  j<Order>(`/api/v2/orders/${id}/?phone=${encodeURIComponent(phone)}`);

export const validateCoupon = (code: string) =>
  j<{ ok: boolean; code?: string; pct?: number; error?: string }>(
    `/api/v2/coupons/validate/?code=${encodeURIComponent(code)}`
  );

export async function uploadReceipt(fd: FormData): Promise<{ ok: boolean; receipt?: unknown; error?: string }> {
  const base = typeof window !== "undefined" ? "" : process.env.API_URL || "http://127.0.0.1:8000";
  const r = await fetch(base + "/api/v2/receipts/", { method: "POST", body: fd });
  return r.json();
}

export const REGIONS = [
  "Toshkent shahri", "Toshkent viloyati", "Samarqand", "Buxoro", "Andijon",
  "Farg'ona", "Namangan", "Qashqadaryo", "Surxondaryo", "Xorazm",
  "Navoiy", "Jizzax", "Sirdaryo", "Qoraqalpog'iston",
];

export const EXPRESS_FEE = 30000;
