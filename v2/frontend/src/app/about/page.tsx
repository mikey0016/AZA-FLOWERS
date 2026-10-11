export default function About() {
  return (
    <div className="container-x py-12 max-w-[760px]">
      <div className="eyebrow">Biz haqimizda</div>
      <h1 className="h-serif text-4xl sm:text-5xl mt-2">Gul emas — hissiyot sovg&apos;a qilamiz</h1>
      <p className="text-stone-600 leading-relaxed mt-4">
        FAX Flores — Toshkentdagi premium gul uyi. Har bir buket floristlarimiz
        tomonidan qo&apos;lda, sevgi bilan yig&apos;iladi. Gollandiya va Ekvador navlari,
        mahalliy issiqxonalar bilan hamkorlik.
      </p>
      <div className="grid sm:grid-cols-2 gap-4 mt-8">
        <div className="card p-6">
          <b className="h-serif text-2xl">Nega biz?</b>
          <ul className="text-sm text-stone-600 leading-loose mt-2 list-disc ml-5">
            <li>Har kuni yangi uzilgan gullar</li>
            <li>Jo&apos;natishdan oldin foto</li>
            <li>3 soatgacha yetkazish</li>
            <li>Otkritka va lenta — bepul</li>
          </ul>
        </div>
        <div className="card p-6">
          <b className="h-serif text-2xl">Kafolat</b>
          <p className="text-sm text-stone-600 leading-relaxed mt-2">
            Fotosidagidan farq qilsa yoki 24 soatda so&apos;lib qolsa —
            almashtirib beramiz yoki pulini qaytaramiz.
          </p>
        </div>
        <div className="card p-6">
          <b className="h-serif text-2xl">To&apos;lov</b>
          <p className="text-sm text-stone-600 leading-relaxed mt-2">
            Naqd 50% oldindan + 50% yetkazishda. Karta 100% oldindan, admin tasdiqlaydi.
          </p>
        </div>
        <div className="card p-6">
          <b className="h-serif text-2xl">Yetkazish</b>
          <p className="text-sm text-stone-600 leading-relaxed mt-2">
            Toshkent bo&apos;ylab Yandex orqali. Standart 3 soat, tezkor 1 soat.
          </p>
        </div>
      </div>
    </div>
  );
}
