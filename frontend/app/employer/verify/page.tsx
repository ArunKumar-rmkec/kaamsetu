"use client";

import { Band, Notice, Shell, Stamp } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import { useState } from "react";

const PASS = {
  aadhaar: "234123412341",
  gstin: "33AABCU9603R1ZM",
  udyam: "UDYAM-TN-07-0012345",
  epfo_id: "CB/CBE/1234567",
};
const FAIL = {
  aadhaar: "900000000000",
  gstin: "33AABCU9603R1ZZ",
  udyam: "NOT-A-UDYAM",
  epfo_id: "BAD",
};

type Check = { passed?: boolean; status?: string; masked?: string; value?: string; rule?: string };

export default function VerifyPage() {
  const { t } = useApp();
  const [form, setForm] = useState(PASS);
  const [result, setResult] = useState<Record<string, Check | string | number | boolean> | null>(null);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    try {
      const data = await api<Record<string, Check | string | number | boolean>>("/api/employers/verify", { method: "POST", body: form });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    }
  }

  const nav = [
    { href: "/employer", label: t("jobs") },
    { href: "/employer/verify", label: t("trust") },
    { href: "/employer/jobs/new", label: t("postJob") },
    { href: "/employer/hires", label: t("hires") },
  ];

  const rows: { key: string; label: string }[] = [
    { key: "aadhaar_ekyc", label: "Aadhaar e-KYC" },
    { key: "gst", label: "GST" },
    { key: "udyam", label: "Udyam" },
    { key: "epfo", label: "EPFO" },
  ];

  return (
    <Shell nav={nav} role="employer">
      <Stamp>API Setu · {t("simulated")}</Stamp>
      <h1 className="mt-2 font-display text-4xl">{t("verifyBiz")}</h1>
      <p className="mt-2 text-sm text-ink/70">
        These four checks return canned results. No government system is contacted. A passing set needs the shapes shown on the sample button.
      </p>
      <div className="mt-4 grid gap-3">
        <Field label="Aadhaar" value={form.aadhaar} onChange={(aadhaar) => setForm({ ...form, aadhaar })} />
        <Field label="GSTIN" value={form.gstin} onChange={(gstin) => setForm({ ...form, gstin })} />
        <Field label="Udyam" value={form.udyam} onChange={(udyam) => setForm({ ...form, udyam })} />
        <Field label="EPFO" value={form.epfo_id} onChange={(epfo_id) => setForm({ ...form, epfo_id })} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="outline" onClick={() => setForm(PASS)}>
          {t("samplePass")}
        </Button>
        <Button variant="outline" onClick={() => setForm(FAIL)}>
          {t("sampleFail")}
        </Button>
        <Button onClick={submit}>{t("submit")}</Button>
      </div>
      {error ? (
        <div className="mt-3">
          <Notice>{error}</Notice>
        </div>
      ) : null}
      {result ? (
        <div className="mt-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-display text-4xl">{String(result.trust_score)}</span>
            <Band band={String(result.trust_band)} />
          </div>
          {rows.map((row) => {
            const check = result[row.key] as Check;
            return (
              <div key={row.key} className="rounded-2xl border border-line bg-card p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{row.label}</span>
                  <span className={check?.passed ? "text-green" : "text-clay"}>{check?.passed ? "Pass" : "Fail"}</span>
                </div>
                <p className="text-ink/60">{check?.masked || check?.status || check?.value}</p>
                <p className="text-xs text-ink/40">{check?.rule}</p>
              </div>
            );
          })}
          <p className="text-xs text-ink/50">{String(result.disclaimer || "")}</p>
        </div>
      ) : null}
    </Shell>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <Label>{label}</Label>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
