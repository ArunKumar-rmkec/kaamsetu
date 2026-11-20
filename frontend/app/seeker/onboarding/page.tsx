"use client";

import { Choice, Notice, Shell } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { SeekerMe } from "@/lib/types";
import { listen } from "@/lib/utils";
import { Mic } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const STEPS = ["you", "skills", "place", "questions", "consent"] as const;

export default function OnboardingPage() {
  const { t, lang, meta } = useApp();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [freeText, setFreeText] = useState("");
  const [form, setForm] = useState({
    name: "",
    district_id: "coimbatore",
    education: "ITI",
    gender: "woman",
    age: 21,
    years_experience: 0,
    expected_wage: 15000,
    shift: "day",
    night_ok: false,
    physical: 3,
    setting: "indoor",
    lodging_needed: false,
    max_commute_km: 25,
    supervision: "either",
    team_size: "small",
    consent: true,
    skills: [] as { code: string; level: number }[],
    answers: {} as Record<string, string>,
  });

  useEffect(() => {
    api<SeekerMe>("/api/seekers/me")
      .then((me) => {
        setForm((current) => ({
          ...current,
          name: me.user.name,
          district_id: me.profile.district_id,
          education: me.profile.education,
          gender: me.profile.gender,
          age: me.profile.age,
          years_experience: me.profile.years_experience,
          expected_wage: me.profile.expected_wage,
          shift: me.profile.shift,
          night_ok: me.profile.night_ok,
          physical: me.profile.physical,
          setting: me.profile.setting,
          lodging_needed: me.profile.lodging_needed,
          max_commute_km: me.profile.max_commute_km,
          supervision: me.profile.supervision,
          team_size: me.profile.team_size,
          consent: me.profile.consent,
          skills: me.skills.map((skill) => ({ code: skill.code, level: skill.level })),
          answers: Object.fromEntries(me.answers.map((item) => [item.question_id, item.answer])),
        }));
      })
      .catch((err) => setError(err.message));
  }, []);

  function setSkill(code: string, level: number | null) {
    setForm((current) => {
      const skills = current.skills.filter((item) => item.code !== code);
      if (level) skills.push({ code, level });
      return { ...current, skills };
    });
  }

  async function mapWords() {
    setError("");
    const result = await api<{ codes: { code: string; level: number; title_en: string }[] }>("/api/agents/map-skill", {
      method: "POST",
      body: { text: freeText, level: 2 },
    });
    for (const code of result.codes) setSkill(code.code, code.level);
  }

  async function save() {
    setBusy(true);
    setError("");
    try {
      await api("/api/seekers/onboarding", {
        method: "POST",
        body: {
          ...form,
          free_text_skill: freeText,
          answers: (meta?.questions ?? []).map((question) => ({
            question_id: question.id,
            answer: form.answers[question.id] || "",
          })),
        },
      });
      router.push("/seeker/profile");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  const nav = [
    { href: "/seeker", label: t("matches") },
    { href: "/seeker/profile", label: t("profile") },
    { href: "/seeker/week", label: t("week") },
    { href: "/seeker/chat", label: t("chat") },
  ];

  return (
    <Shell nav={nav} role="seeker">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-green">
        {step + 1} / {STEPS.length}
      </p>
      <h1 className="mt-1 font-display text-4xl">{step === 0 ? t("profile") : step === 1 ? t("skills") : step === 2 ? t("workplace") : step === 3 ? t("questions") : t("consent")}</h1>
      <div className="mt-3 flex gap-1">
        {STEPS.map((item, index) => (
          <span key={item} className={`h-1.5 flex-1 rounded-full ${index <= step ? "bg-green" : "bg-ink/10"}`} />
        ))}
      </div>
      <div className="mt-5 space-y-4">
        {step === 0 ? (
          <>
            <Field label={t("name")}>
              <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
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
            <div className="grid grid-cols-2 gap-2">
              {["10th", "12th", "ITI", "Diploma", "College"].map((item) => (
                <Choice key={item} active={form.education === item} onClick={() => setForm({ ...form, education: item })}>
                  {item}
                </Choice>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2">
              {["woman", "man", "other"].map((item) => (
                <Choice key={item} active={form.gender === item} onClick={() => setForm({ ...form, gender: item })}>
                  {item}
                </Choice>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("age")}>
                <Input type="number" value={form.age} onChange={(event) => setForm({ ...form, age: Number(event.target.value) })} />
              </Field>
              <Field label={t("experience")}>
                <Input type="number" value={form.years_experience} onChange={(event) => setForm({ ...form, years_experience: Number(event.target.value) })} />
              </Field>
            </div>
          </>
        ) : null}
        {step === 1 ? (
          <>
            <Field label={t("map")}>
              <Textarea value={freeText} onChange={(event) => setFreeText(event.target.value)} placeholder="sewing machine, bike mechanic…" />
            </Field>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={mapWords}>
                {t("map")}
              </Button>
              <MicButton
                onText={(text) => setFreeText((current) => (current ? `${current} ${text}` : text))}
              />
            </div>
            <div className="space-y-2">
              {(meta?.taxonomy ?? []).map((skill) => {
                const selected = form.skills.find((item) => item.code === skill.code);
                return (
                  <div key={skill.code} className="rounded-2xl border border-line bg-card p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="font-semibold">{lang === "ta" ? skill.title_ta : skill.title_en}</div>
                        <div className="text-xs text-ink/50">{skill.code}</div>
                      </div>
                      <Choice active={!!selected} onClick={() => setSkill(skill.code, selected ? null : 2)}>
                        {selected ? "On" : "Add"}
                      </Choice>
                    </div>
                    {selected ? (
                      <div className="mt-2 flex gap-1">
                        {[1, 2, 3, 4, 5].map((level) => (
                          <Choice key={level} active={selected.level === level} onClick={() => setSkill(skill.code, level)}>
                            {level}
                          </Choice>
                        ))}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </>
        ) : null}
        {step === 2 ? (
          <>
            <Field label={t("wage")}>
              <Input type="number" value={form.expected_wage} onChange={(event) => setForm({ ...form, expected_wage: Number(event.target.value) })} />
            </Field>
            <Label>{t("shift")}</Label>
            <div className="grid grid-cols-3 gap-2">
              {["day", "rotating", "night"].map((item) => (
                <Choice key={item} active={form.shift === item} onClick={() => setForm({ ...form, shift: item })}>
                  {item}
                </Choice>
              ))}
            </div>
            <Toggle label={t("night")} checked={form.night_ok} onChange={(night_ok) => setForm({ ...form, night_ok })} />
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
            <Toggle label={t("lodging")} checked={form.lodging_needed} onChange={(lodging_needed) => setForm({ ...form, lodging_needed })} />
            <Field label={t("commute")}>
              <div className="grid grid-cols-3 gap-2">
                {[10, 15, 25, 40, 60, 80].map((item) => (
                  <Choice key={item} active={form.max_commute_km === item} onClick={() => setForm({ ...form, max_commute_km: item })}>
                    {item}
                  </Choice>
                ))}
              </div>
            </Field>
            <Label>{t("supervision")}</Label>
            <div className="grid grid-cols-3 gap-2">
              {["close", "independent", "either"].map((item) => (
                <Choice key={item} active={form.supervision === item} onClick={() => setForm({ ...form, supervision: item })}>
                  {item}
                </Choice>
              ))}
            </div>
            <Label>{t("team")}</Label>
            <div className="grid grid-cols-4 gap-2">
              {["solo", "small", "large", "any"].map((item) => (
                <Choice key={item} active={form.team_size === item} onClick={() => setForm({ ...form, team_size: item })}>
                  {item}
                </Choice>
              ))}
            </div>
          </>
        ) : null}
        {step === 3 ? (
          <div className="space-y-4">
            {(meta?.questions ?? []).map((question) => (
              <div key={question.id}>
                <Label>{lang === "ta" ? question.prompt_ta : question.prompt_en}</Label>
                <Textarea
                  className="mt-2"
                  value={form.answers[question.id] || ""}
                  onChange={(event) => setForm({ ...form, answers: { ...form.answers, [question.id]: event.target.value } })}
                />
                <div className="mt-2">
                  <MicButton
                    onText={(text) =>
                      setForm((current) => ({
                        ...current,
                        answers: { ...current.answers, [question.id]: current.answers[question.id] ? `${current.answers[question.id]} ${text}` : text },
                      }))
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {step === 4 ? (
          <div className="rounded-3xl border border-line bg-card p-4">
            <Toggle label={t("consent")} checked={form.consent} onChange={(consent) => setForm({ ...form, consent })} />
            <p className="mt-3 text-sm text-ink/70">
              Employers see a code, your district, skill bands, and the reasons. Your name and phone stay hidden until you accept their interest.
            </p>
          </div>
        ) : null}
        {error ? <Notice>{error}</Notice> : null}
        <div className="flex gap-2">
          {step > 0 ? (
            <Button type="button" variant="outline" onClick={() => setStep((value) => value - 1)}>
              {t("back")}
            </Button>
          ) : null}
          {step < 4 ? (
            <Button type="button" onClick={() => setStep((value) => value + 1)}>
              {t("next")}
            </Button>
          ) : (
            <Button type="button" disabled={busy} onClick={save}>
              {t("save")}
            </Button>
          )}
        </div>
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

function MicButton({ onText }: { onText: (text: string) => void }) {
  const { lang } = useApp();
  const [supported, setSupported] = useState(false);
  useEffect(() => {
    const host = window as Window & { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown };
    setSupported(Boolean(host.SpeechRecognition || host.webkitSpeechRecognition));
  }, []);
  if (!supported) return null;
  return (
    <Button type="button" variant="outline" size="sm" onClick={() => listen(lang, onText)}>
      <Mic className="h-4 w-4" />
      Voice
    </Button>
  );
}
