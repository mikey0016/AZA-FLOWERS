"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, register } = useAuth();
  const [tab, setTab] = useState<"login" | "reg">("login");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) {
    router.replace("/cabinet");
    return null;
  }

  const go = async () => {
    setErr("");
    if (phone.replace(/\D/g, "").length < 9 || !pw) return setErr("Telefon va parolni kiriting");
    if (tab === "reg" && name.trim().length < 2) return setErr("Ismingizni yozing");
    setBusy(true);
    const e = tab === "login" ? await login(phone.trim(), pw) : await register(name.trim(), phone.trim(), pw);
    setBusy(false);
    if (e) setErr(e);
    else router.push("/cabinet");
  };

  return (
    <div className="container-x py-12 max-w-[440px]">
      <h1 className="h-serif text-4xl text-center">Xush kelibsiz</h1>
      <div className="flex gap-2 my-5">
        {(["login", "reg"] as const).map((x) => (
          <button key={x} onClick={() => { setTab(x); setErr(""); }}
            className={`flex-1 border rounded-xl py-2.5 font-semibold ${tab === x ? "bg-forest text-white border-forest" : "border-beige"}`}>
            {x === "login" ? "Kirish" : "Ro'yxatdan o'tish"}
          </button>
        ))}
      </div>
      <div className="grid gap-3">
        {tab === "reg" && (
          <label className="field"><span>Ism *</span>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ismingiz" /></label>
        )}
        <label className="field"><span>Telefon *</span>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998 ..." inputMode="tel" /></label>
        <label className="field"><span>Parol *</span>
          <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} placeholder={tab === "reg" ? "Kamida 4 belgi" : "Parol"} /></label>
        {err && <p className="text-red-600 text-sm">⛔ {err}</p>}
        <button disabled={busy} onClick={go} className="btn btn-primary w-full disabled:opacity-40">
          {busy ? "..." : tab === "login" ? "Kirish →" : "Ro'yxatdan o'tish →"}
        </button>
      </div>
    </div>
  );
}
