"use client";

import { Choice, Notice, Shell } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { HireRow } from "@/lib/types";
import { useEffect, useState } from "react";

export default function WeekPage() {
  const { t } = useApp();
  const [mood, setMood] = useState("good");
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [hires, setHires] = useState<HireRow[]>([]);
  const [clock, setClock] = useState<{ week: number; day: number } | null>(null);
  const [drafts, setDrafts] = useState<Record<string, { rating: number; comment: string }>>({});

  async function load() {
    const data = await api<{ hires: HireRow[]; clock: { week: number; day: number } }>("/api/seekers/hires");
    setHires(data.hires);
    setClock(data.clock);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function checkin() {
    setError("");
    try {
      const result = await api<{ streak: number }>("/api/seekers/checkin", { method: "POST", body: { mood, note } });
      setMessage(`Checked in. Streak ${result.streak}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check-in failed");
    }
  }

  async function send(hireId: number, week: number) {
    const draft = drafts[`${hireId}-${week}`] ?? { rating: 4, comment: "" };
    await api("/api/seekers/feedback", {
      method: "POST",
      body: { hire_id: hireId, week, rating: draft.rating, comment: draft.comment },
    });
    await load();
  }

  const nav = [
    { href: "/seeker", label: t("matches") },
    { href: "/seeker/profile", label: t("profile") },
    { href: "/seeker/week", label: t("week") },
    { href: "/seeker/chat", label: t("chat") },
  ];

  return (
    <Shell nav={nav} role="seeker">
      <h1 className="font-display text-4xl">{t("checkIn")}</h1>
      {clock ? (
        <p className="text-sm text-ink/60">
          Week {clock.week} · Day {clock.day}
        </p>
      ) : null}
      <div className="mt-4 grid grid-cols-3 gap-2">
        {[
          ["good", t("moodGood")],
          ["okay", t("moodOkay")],
          ["tough", t("moodTough")],
        ].map(([value, label]) => (
          <Choice key={value} active={mood === value} onClick={() => setMood(value)}>
            {label}
          </Choice>
        ))}
      </div>
      <Textarea className="mt-3" placeholder={t("note")} value={note} onChange={(event) => setNote(event.target.value)} />
      <Button className="mt-3" onClick={checkin}>
        {t("submit")}
      </Button>
      {message ? (
        <div className="mt-3">
          <Notice tone="green">{message}</Notice>
        </div>
      ) : null}
      {error ? (
        <div className="mt-3">
          <Notice>{error}</Notice>
        </div>
      ) : null}
      <h2 className="mt-8 font-display text-3xl">{t("feedback")}</h2>
      <p className="text-sm text-ink/60">{t("blind")}</p>
      {!hires.length ? <p className="mt-2 text-sm text-ink/70">{t("emptyHires")}</p> : null}
      <div className="mt-3 space-y-3">
        {hires.map((hire) => (
          <article key={hire.id} className="rounded-3xl border border-line bg-card p-4">
            <h3 className="font-display text-2xl leading-none">{hire.job_title}</h3>
            <p className="text-sm text-ink/60">{hire.company}</p>
            <FeedbackList
              hire={hire}
              viewer="seeker"
              clockWeek={clock?.week ?? hire.week_hired}
              drafts={drafts}
              setDrafts={setDrafts}
              onSend={send}
            />
          </article>
        ))}
      </div>
    </Shell>
  );
}

export function FeedbackList({
  hire,
  viewer,
  clockWeek,
  drafts,
  setDrafts,
  onSend,
}: {
  hire: HireRow;
  viewer: "seeker" | "employer";
  clockWeek: number;
  drafts: Record<string, { rating: number; comment: string }>;
  setDrafts: React.Dispatch<React.SetStateAction<Record<string, { rating: number; comment: string }>>>;
  onSend: (hireId: number, week: number) => Promise<void>;
}) {
  const { t } = useApp();
  const weeks = [];
  for (let week = hire.week_hired; week <= clockWeek; week += 1) weeks.push(week);
  return (
    <div className="mt-3 space-y-3">
      {weeks.map((week) => {
        const mine = hire.feedback.find((item) => item.week === week && item.author_role === viewer);
        const theirs = hire.feedback.find((item) => item.week === week && item.author_role !== viewer);
        const key = `${hire.id}-${week}`;
        const draft = drafts[key] ?? { rating: mine?.rating ?? 4, comment: mine?.comment ?? "" };
        return (
          <div key={week} className="rounded-2xl bg-paper p-3">
            <div className="text-xs font-bold uppercase tracking-wide text-ink/50">Week {week}</div>
            {theirs?.hidden ? <p className="mt-1 text-sm">{t("hidden")}</p> : null}
            {theirs && !theirs.hidden ? (
              <p className="mt-1 text-sm">
                {t("revealed")}: {theirs.rating}/5 — {theirs.comment}
              </p>
            ) : null}
            <div className="mt-2 flex gap-1">
              {[1, 2, 3, 4, 5].map((rating) => (
                <Choice
                  key={rating}
                  active={draft.rating === rating}
                  onClick={() => setDrafts((current) => ({ ...current, [key]: { ...draft, rating } }))}
                >
                  {rating}
                </Choice>
              ))}
            </div>
            <Textarea
              className="mt-2"
              value={draft.comment}
              onChange={(event) => setDrafts((current) => ({ ...current, [key]: { ...draft, comment: event.target.value } }))}
            />
            <Button className="mt-2" size="sm" onClick={() => onSend(hire.id, week)}>
              {t("submit")}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
