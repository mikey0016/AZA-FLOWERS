export default function Contact() {
  return (
    <div className="container-x py-12 max-w-[680px]">
      <div className="eyebrow">Aloqa</div>
      <h1 className="h-serif text-4xl sm:text-5xl mt-2">Bog&apos;laning</h1>
      <div className="card p-6 mt-6 grid gap-2 text-[15px]">
        <div>📞 <a href="tel:+998903507178" className="font-semibold text-forest">+998 90 350 71 78</a></div>
        <div>📍 Toshkent sh., Chilonzor tumani, Bunyodkor shoh ko&apos;chasi 12</div>
        <div>🕗 Har kuni 08:00 – 22:00</div>
        <div className="flex gap-2 mt-2">
          <a href="https://t.me/azaflowers" target="_blank" className="btn btn-primary !py-3 text-sm">Telegram yozish</a>
          <a href="https://instagram.com/aza.flowers" target="_blank" className="btn btn-outline !py-3 text-sm">Instagram</a>
        </div>
      </div>
    </div>
  );
}
