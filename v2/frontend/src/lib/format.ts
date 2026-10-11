export function uzs(v: number | string): string {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (Number.isNaN(n)) return "0 so'm";
  return Math.round(n).toLocaleString("uz-UZ").replace(/,/g, " ") + " so'm";
}
