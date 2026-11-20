"use client";

import { LangToggle, Notice } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { SessionUser } from "@/lib/types";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

const DEMOS = [
  { role: "seeker", phone: "9840011101", name: "Priya Selvam", company: "" },
  { role: "employer", phone: "9840022202", name: "Annamalai", company: "Annamalai Textiles" },
  { role: "official", phone: "9840033303", name: "District Employment Desk", company: "" },
];

function LoginForm() {
  const params = useSearchParams();
  const role = (params.get("role") || "seeker") as SessionUser["role"];
  const demo = DEMOS.find((item) => item.role === role) ?? DEMOS[0];
  const { t, setUser, meta } = useApp();
  const router = useRouter();
  const [phone, setPhone] = useState(demo.phone);
  const [name, setName] = useState(demo.name);
  const [company, setCompany] = useState(demo.company);
  const [district, setDistrict] = useState("coimbatore");
  const [otp, setOtp] = useState("123456");
  const [hint, setHint] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    setError("");
    const result = await api<{ hint: string }>("/api/auth/request-otp", { method: "POST", body: { phone, role } });
    setHint(result.hint);
  }

  async function verify() {
    setBusy(true);
    setError("");
    try {
      const result = await api<{ token: string; user: SessionUser }>("/api/auth/verify-otp", {
        method: "POST",
        body: { phone, otp, role, name, company_name: company, district_id: district },
      });
      localStorage.setItem("ks_token", result.token);
      setUser(result.user);
      router.push(role === "seeker" ? "/seeker" : role === "employer" ? "/employer" : "/officials");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      <div className="mb-4 flex justify-end">
        <LangToggle />
      </div>
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-green">{t("simulated")}</p>
      <h1 className="mt-2 font-display text-4xl">{role === "seeker" ? t("seeker") : role === "employer" ? t("employer") : t("official")}</h1>
      <p className="mt-2 text-sm text-ink/70">No SMS leaves this machine. The mock code is {meta?.otp_hint ?? "123456"}.</p>
      <div className="mt-5 space-y-3">
        <div>
          <Label>{t("phone")}</Label>
          <Input value={phone} onChange={(event) => setPhone(event.target.value)} inputMode="numeric" />
        </div>
        <div>
          <Label>{t("name")}</Label>
          <Input value={name} onChange={(event) => setName(event.target.value)} />
        </div>
        {role === "employer" ? (
          <div>
            <Label>{t("company")}</Label>
            <Input value={company} onChange={(event) => setCompany(event.target.value)} />
          </div>
        ) : null}
        {role !== "official" ? (
          <div>
            <Label>{t("district")}</Label>
            <select className="h-12 w-full rounded-2xl border border-line bg-card px-3" value={district} onChange={(event) => setDistrict(event.target.value)}>
              {(meta?.districts ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name_en}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <Button type="button" variant="outline" onClick={send}>
          {t("sendOtp")}
        </Button>
        {hint ? <Notice tone="green">Mock OTP: {hint}</Notice> : null}
        <div>
          <Label>{t("otp")}</Label>
          <Input value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" />
        </div>
        {error ? <Notice>{error}</Notice> : null}
        <Button type="button" className="w-full" disabled={busy} onClick={verify}>
          {t("verify")}
        </Button>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
