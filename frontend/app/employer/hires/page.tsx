"use client";

import { FeedbackList } from "@/app/seeker/week/page";
import { Notice, Shell } from "@/components/bits";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { HireRow } from "@/lib/types";
import { useEffect, useState } from "react";

export default function EmployerHires() {
  const { t } = useApp();
  const [hires, setHires] = useState<HireRow[]>([]);
  const [clock, setClock] = useState<{ week: number; day: number } | null>(null);
  const [drafts, setDrafts] = useState<Record<string, { rating: number; comment: string }>>({});
  const [error, setError] = useState("");

  async function load() {
    const data = await api<{ hires: HireRow[]; clock: { week: number; day: number } }>("/api/employers/hires");
    setHires(data.hires);
    setClock(data.clock);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function send(hireId: number, week: number) {
    const draft = drafts[`${hireId}-${week}`] ?? { rating: 4, comment: "" };
    await api("/api/employers/feedback", { method: "POST", body: { hire_id: hireId, week, rating: draft.rating, comment: draft.comment } });
    await load();
  }

  const nav = [
    { href: "/employer", label: t("jobs") },
    { href: "/employer/verify", label: t("trust") },
    { href: "/employer/jobs/new", label: t("postJob") },
    { href: "/employer/hires", label: t("hires") },
  ];

  return (
    <Shell nav={nav} role="employer">
      <h1 className="font-display text-4xl">{t("hires")}</h1>
      <p className="text-sm text-ink/60">A rating stays hidden until the other side has filed the same week. Scores move only then.</p>
      {error ? (
        <div className="mt-3">
          <Notice>{error}</Notice>
        </div>
      ) : null}
      {!hires.length ? <p className="mt-4 text-sm">{t("emptyHires")}</p> : null}
      <div className="mt-4 space-y-3">
        {hires.map((hire) => (
          <article key={hire.id} className="rounded-3xl border border-line bg-card p-4">
            <h2 className="font-display text-2xl leading-none">{hire.seeker_name}</h2>
            <p className="text-sm text-ink/60">{hire.job_title}</p>
            <FeedbackList hire={hire} viewer="employer" clockWeek={clock?.week ?? hire.week_hired} drafts={drafts} setDrafts={setDrafts} onSend={send} />
          </article>
        ))}
      </div>
    </Shell>
  );
}
