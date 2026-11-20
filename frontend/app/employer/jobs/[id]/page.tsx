"use client";

import { Band, DistrictText, FitBar, Notice, Reasons, Shell, Stamp } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { Candidate } from "@/lib/types";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function CandidatesPage() {
  const { t, lang } = useApp();
  const params = useParams<{ id: string }>();
  const [title, setTitle] = useState("");
  const [rows, setRows] = useState<Candidate[]>([]);
  const [error, setError] = useState("");

  async function load() {
    const data = await api<{ job: { title: string }; candidates: Candidate[] }>(`/api/employers/jobs/${params.id}/candidates`);
    setTitle(data.job.title);
    setRows(data.candidates);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [params.id]);

  async function act(matchId: number, action: "interest" | "hire") {
    setError("");
    try {
      await api(`/api/employers/matches/${matchId}/${action}`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update");
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
      <Stamp>{t("simulated")}</Stamp>
      <h1 className="mt-2 font-display text-4xl leading-none">{title || t("candidates")}</h1>
      <p className="mt-2 text-sm text-ink/70">Names stay off the card until the seeker accepts. Bands are shown, not raw phone numbers.</p>
      {error ? (
        <div className="mt-3">
          <Notice>{error}</Notice>
        </div>
      ) : null}
      <div className="mt-4 space-y-3">
        {rows.map((row) => (
          <article key={row.match_id} className="rounded-3xl border border-line bg-card p-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-display text-2xl leading-none">{row.revealed ? row.name : row.candidate_ref}</h2>
                <p className="mt-1 text-sm text-ink/60">
                  <DistrictText id={row.district_id} /> · {row.age_band} · {row.education}
                  {row.revealed ? ` · ${row.phone}` : ""}
                </p>
              </div>
              <span className="text-xs font-bold uppercase text-ink/50">{row.status}</span>
            </div>
            <div className="mt-2 flex gap-2">
              <Band band={row.skill_band} />
              <Band band={row.potential_band} />
            </div>
            <ul className="mt-3 text-sm">
              {row.skills.map((skill) => (
                <li key={skill.code}>
                  {lang === "ta" ? skill.title_ta : skill.title_en} · {skill.level}/5
                </li>
              ))}
            </ul>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <FitBar label="Skill" value={row.fits.skill} />
              <FitBar label="Place" value={row.fits.environment} />
              <FitBar label="Pay" value={row.fits.pay} />
            </div>
            <div className="mt-3">
              <Reasons items={row.reasons} />
            </div>
            <div className="mt-3 flex gap-2">
              {row.status === "allocated" ? <Button onClick={() => act(row.match_id, "interest")}>{t("interest")}</Button> : null}
              {row.status === "interested" ? <p className="text-sm text-ink/60">{t("waiting")} for the seeker.</p> : null}
              {row.status === "accepted" ? <Button onClick={() => act(row.match_id, "hire")}>{t("hire")}</Button> : null}
            </div>
          </article>
        ))}
        {!rows.length ? <p className="text-sm text-ink/60">No one is allocated to this opening. Flagged listings are kept off the feed.</p> : null}
      </div>
    </Shell>
  );
}
