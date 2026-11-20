"use client";

import { Choice, Notice, Shell } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { JobCard } from "@/lib/types";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewJobPage() {
  const { t, lang, meta } = useApp();
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<string>("");
  const [form, setForm] = useState({
    title: "Sewing machine operator",
    sector: "garments",
    district_id: "coimbatore",
    description: "Day-shift stitching on a single-needle machine. Close supervision for the first month.",
    salary_min: 14000,
    salary_max: 16000,
    hike_pct: 5,
    perks: "Canteen",
    negotiation_low: 13500,
    negotiation_high: 16500,
    open_to_freshers: true,
    will_train: true,
    openings: 2,
    shift: "day",
    night_required: false,
    physical: 2,
    setting: "indoor",
    lodging_provided: false,
    supervision: "close",
    team_size: "small",
    skills: [{ code: "8152.02", min_level: 2, required: true }] as { code: string; min_level: number; required: boolean }[],
    demo_mismatch: false,
  });
  const [file, setFile] = useState<File | null>(null);

  function toggleSkill(code: string) {
    setForm((current) => {
      const exists = current.skills.some((item) => item.code === code);
      return {
        ...current,
        skills: exists ? current.skills.filter((item) => item.code !== code) : [...current.skills, { code, min_level: 2, required: true }],
      };
    });
  }

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const data = new FormData();
      const { skills, demo_mismatch, ...rest } = form;
      Object.entries(rest).forEach(([key, value]) => data.append(key, String(value)));
      data.append("skills_json", JSON.stringify(skills));
      data.append("demo_mismatch", String(demo_mismatch));
      if (file) data.append("video", file);
      const result = await api<{ job: JobCard; verification: { summary_en: string; summary_ta: string; status: string; label: string } }>(
        "/api/jobs",
        { method: "POST", form: data },
      );
      setReport(`${result.verification.status} · ${result.verification.label}: ${lang === "ta" ? result.verification.summary_ta : result.verification.summary_en}`);
      router.push(`/employer/jobs/${result.job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not post");
    } finally {
      setBusy(false);
    }
  }

  const nav = [
    { href: "/employer", label: t("jobs") },
    { href: "/employer/verify", label: t("trust") },
    { href: "/employer/jobs/new", label: t("postJob") },
    { href: "/employer/hires", label: t("hires") },
  ];

  return (
    <Shell nav={nav} role="employer">
      <h1 className="font-display text-4xl">{t("postJob")}</h1>
      <div className="mt-4 space-y-3">
        <Field label="Title">
          <Input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        </Field>
        <Field label={t("district")}>
          <select className="h-12 w-full rounded-2xl border border-line bg-card px-3" value={form.district_id} onChange={(event) => setForm({ ...form, district_id: event.target.value })}>
            {(meta?.districts ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {lang === "ta" ? item.name_ta : item.name_en}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Sector">
          <select className="h-12 w-full rounded-2xl border border-line bg-card px-3" value={form.sector} onChange={(event) => setForm({ ...form, sector: event.target.value })}>
            {(meta?.sectors ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {lang === "ta" ? item.ta : item.en}
              </option>
            ))}
          </select>
        </Field>
        <Textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        <div className="grid grid-cols-2 gap-2">
          <Field label={t("salary") + " min"}>
            <Input type="number" value={form.salary_min} onChange={(event) => setForm({ ...form, salary_min: Number(event.target.value) })} />
          </Field>
          <Field label="max">
            <Input type="number" value={form.salary_max} onChange={(event) => setForm({ ...form, salary_max: Number(event.target.value) })} />
          </Field>
          <Field label={t("negotiate") + " low"}>
            <Input type="number" value={form.negotiation_low} onChange={(event) => setForm({ ...form, negotiation_low: Number(event.target.value) })} />
          </Field>
          <Field label="high">
            <Input type="number" value={form.negotiation_high} onChange={(event) => setForm({ ...form, negotiation_high: Number(event.target.value) })} />
          </Field>
        </div>
        <Field label={t("hike")}>
          <Input type="number" value={form.hike_pct} onChange={(event) => setForm({ ...form, hike_pct: Number(event.target.value) })} />
        </Field>
        <Field label={t("perks")}>
          <Input value={form.perks} onChange={(event) => setForm({ ...form, perks: event.target.value })} />
        </Field>
        <Toggle label={t("freshers")} checked={form.open_to_freshers} onChange={(open_to_freshers) => setForm({ ...form, open_to_freshers })} />
        <Toggle label={t("train")} checked={form.will_train} onChange={(will_train) => setForm({ ...form, will_train })} />
        <Field label={t("openings")}>
          <Input type="number" value={form.openings} onChange={(event) => setForm({ ...form, openings: Number(event.target.value) })} />
        </Field>
        <Label>{t("shift")}</Label>
        <div className="grid grid-cols-3 gap-2">
          {["day", "rotating", "night"].map((item) => (
            <Choice key={item} active={form.shift === item} onClick={() => setForm({ ...form, shift: item })}>
              {item}
            </Choice>
          ))}
        </div>
        <Toggle label={t("night")} checked={form.night_required} onChange={(night_required) => setForm({ ...form, night_required })} />
        <Label>{t("physical")}</Label>
        <div className="grid grid-cols-5 gap-2">
          {[1, 2, 3, 4, 5].map((item) => (
            <Choice key={item} active={form.physical === item} onClick={() => setForm({ ...form, physical: item })}>
              {item}
            </Choice>
          ))}
        </div>
        <Label>{t("setting")}</Label>
        <div className="grid grid-cols-3 gap-2">
          {["indoor", "outdoor", "either"].map((item) => (
            <Choice key={item} active={form.setting === item} onClick={() => setForm({ ...form, setting: item })}>
              {item}
            </Choice>
          ))}
        </div>
        <Toggle label={t("lodging")} checked={form.lodging_provided} onChange={(lodging_provided) => setForm({ ...form, lodging_provided })} />
        <Label>{t("supervision")}</Label>
        <div className="grid grid-cols-3 gap-2">
          {["close", "independent", "either"].map((item) => (
            <Choice key={item} active={form.supervision === item} onClick={() => setForm({ ...form, supervision: item })}>
              {item}
            </Choice>
          ))}
        </div>
        <Label>{t("team")}</Label>
        <div className="grid grid-cols-3 gap-2">
          {["solo", "small", "large"].map((item) => (
            <Choice key={item} active={form.team_size === item} onClick={() => setForm({ ...form, team_size: item })}>
              {item}
            </Choice>
          ))}
        </div>
        <Label>{t("skills")}</Label>
        <div className="flex flex-wrap gap-2">
          {(meta?.taxonomy ?? []).map((skill) => {
            const on = form.skills.some((item) => item.code === skill.code);
            return (
              <button key={skill.code} type="button" onClick={() => toggleSkill(skill.code)} className={`rounded-full border px-3 py-2 text-xs font-semibold ${on ? "border-green bg-green text-paper" : "border-line bg-card"}`}>
                {lang === "ta" ? skill.title_ta : skill.title_en}
              </button>
            );
          })}
        </div>
        <Field label={t("video")}>
          <Input type="file" accept="video/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </Field>
        <p className="text-xs text-ink/50">If you skip the file, a stored sample clip is kept and the checker uses mock video tags. A vision model runs only when OPENAI_API_KEY is set.</p>
        <Toggle label={t("mismatch")} checked={form.demo_mismatch} onChange={(demo_mismatch) => setForm({ ...form, demo_mismatch })} />
        {error ? <Notice>{error}</Notice> : null}
        {report ? <Notice tone="green">{report}</Notice> : null}
        <Button disabled={busy} onClick={submit}>
          {t("submit")}
        </Button>
      </div>
    </Shell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-card px-3 py-3">
      <span className="text-sm font-semibold">{label}</span>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}
