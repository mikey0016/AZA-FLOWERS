import type { Metadata } from "next";
import { LangProvider } from "@/lib/i18n";
import { ShopProvider } from "@/lib/shop";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "AZA FLOWERS — Premium gullar Toshkentda",
  description: "Premium buketlar: atirgul, lola, pion. Har kuni 08:00–22:00.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Manrope:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <LangProvider>
          <ShopProvider>
            <Header />
            <main className="min-h-[60vh]">{children}</main>
            <Footer />
          </ShopProvider>
        </LangProvider>
      </body>
    </html>
  );
}
