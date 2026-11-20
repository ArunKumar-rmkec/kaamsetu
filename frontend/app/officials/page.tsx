"use client";

import { Notice, Shell, Stamp } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import { useEffect, useState } from "react";

type Overview = {
  label: string;
  clock: { week: number; day: number };
  counts: { seekers: number; jobs: number; open_jobs: number; flagged: number; hires: number; matches: number };
  fairness: {
    gini: number;
    first_time_hire_share: number;
    hire_count: number;
    mean_time_to_first_match_weeks: number | null;
    exposure: { share_with_zero_exposure: number; share_with_at_least_one: number; mean_exposure: number };
  };
  districts: { id: string; name_en: string; name_ta: string; seekers: number; jobs: number; mean_exposure: number; zero_exposure: number }[];
  flagged_listings: { job_id: number; title: string; company: string; district_id: string; source: string; report: { summary_en?: string } }[];
  latest_simulation: Simulation | null;
};

type Arm = {
  gini: number;
  share_with_at_least_one: number;
  share_with_zero_exposure: number;
  first_time_hire_share: number;
  mean_time_to_first_match_weeks: number | null;
  mean_relevance: number;
  high_potential_fresher_train_coverage: number | null;
  hires: number;
};

type Simulation = {
  label: string;
  disclaimer: string;
  seekers: number;
  jobs: number;
  ranking: Arm;
  kaamsetu: Arm;
  read: string[];
};

export default function OfficialsPage() {
  const { t, lang } = useApp();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  async function load() {
    setData(await api<Overview>("/api/officials/overview"));
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function run(path: string, label: string) {
    setBusy(label);
    setError("");
    try {
      await api(path, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy("");
    }
  }

  const nav = [
    { href: "/officials", label: t("fairness") },
    { href: "/officials", label: t("flagged") },
  ];

  return (
    <Shell nav={nav} wide role="official">
      <Stamp>{data?.label ?? t("simulated")}</Stamp>
      <h1 className="mt-2 font-display text-4xl">{t("fairness")}</h1>
      {data ? (
        <p className="text-sm text-ink/60">
          Week {data.clock.week} · Day {data.clock.day} · {data.counts.seekers} seekers · {data.counts.jobs} jobs
        </p>
      ) : (
        <p>Loading the district desk…</p>
      )}
      {error ? (
        <div className="mt-3">
          <Notice>{error}</Notice>
        </div>
      ) : null}
      {data ? (
        <>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Metric label="Exposure Gini" value={data.fairness.gini.toFixed(2)} />
            <Metric label="First-job share of hires" value={`${Math.round(data.fairness.first_time_hire_share * 100)}%`} />
            <Metric label="Weeks to first match" value={data.fairness.mean_time_to_first_match_weeks?.toFixed(1) ?? "—"} />
            <Metric label="Never shown" value={`${Math.round(data.fairness.exposure.share_with_zero_exposure * 100)}%`} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" disabled={!!busy} onClick={() => run("/api/officials/clock/day", "day")}>
              {busy === "day" ? "…" : t("advanceDay")}
            </Button>
            <Button variant="outline" disabled={!!busy} onClick={() => run("/api/officials/clock/week", "week")}>
              {busy === "week" ? "…" : t("advanceWeek")}
            </Button>
            <Button variant="outline" disabled={!!busy} onClick={() => run("/api/officials/matching/run", "match")}>
              {busy === "match" ? "…" : t("runMatch")}
            </Button>
            <Button disabled={!!busy} onClick={() => run("/api/officials/simulate", "sim")}>
              {busy === "sim" ? "Running…" : t("simulate")}
            </Button>
          </div>
          <h2 className="mt-8 font-display text-2xl">By district</h2>
          <div className="mt-2 overflow-x-auto rounded-3xl border border-line bg-card">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-3 py-2">District</th>
                  <th className="px-3 py-2">Seekers</th>
                  <th className="px-3 py-2">Jobs</th>
                  <th className="px-3 py-2">Mean shown</th>
                  <th className="px-3 py-2">Never shown</th>
                </tr>
              </thead>
              <tbody>
                {data.districts.map((row) => (
                  <tr key={row.id} className="border-t border-line">
                    <td className="px-3 py-2 font-semibold">{lang === "ta" ? row.name_ta : row.name_en}</td>
                    <td className="px-3 py-2">{row.seekers}</td>
                    <td className="px-3 py-2">{row.jobs}</td>
                    <td className="px-3 py-2">{row.mean_exposure}</td>
                    <td className="px-3 py-2">{row.zero_exposure}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h2 className="mt-8 font-display text-2xl">{t("flagged")}</h2>
          <div className="mt-2 space-y-2">
            {data.flagged_listings.map((row) => (
              <article key={row.job_id} className="rounded-2xl border border-clay/40 bg-card p-3 text-sm">
                <div className="font-semibold">
                  {row.title} · {row.company}
                </div>
                <p className="text-ink/70">{row.report.summary_en}</p>
                <p className="text-xs uppercase tracking-wide text-clay">{row.source}</p>
              </article>
            ))}
          </div>
          {data.latest_simulation ? <Compare report={data.latest_simulation} /> : <p className="mt-6 text-sm text-ink/60">The four-week comparison has not been run in this database yet.</p>}
        </>
      ) : null}
    </Shell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-line bg-card p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-ink/50">{label}</div>
      <div className="font-display text-3xl leading-none">{value}</div>
    </div>
  );
}

function Compare({ report }: { report: Simulation }) {
  const rows: { label: string; rank: number; fair: number; percent?: boolean }[] = [
    { label: "Exposure Gini (lower is fairer)", rank: report.ranking.gini, fair: report.kaamsetu.gini },
    { label: "Seekers with ≥1 recommendation", rank: report.ranking.share_with_at_least_one, fair: report.kaamsetu.share_with_at_least_one, percent: true },
    { label: "First-time share of hires", rank: report.ranking.first_time_hire_share, fair: report.kaamsetu.first_time_hire_share, percent: true },
    { label: "Weeks to first match", rank: report.ranking.mean_time_to_first_match_weeks ?? 0, fair: report.kaamsetu.mean_time_to_first_match_weeks ?? 0 },
    { label: "High-potential freshers on a training job", rank: report.ranking.high_potential_fresher_train_coverage ?? 0, fair: report.kaamsetu.high_potential_fresher_train_coverage ?? 0, percent: true },
    { label: "Mean relevance of assignments", rank: report.ranking.mean_relevance, fair: report.kaamsetu.mean_relevance },
  ];
  return (
    <section className="mt-8">
      <Stamp>{report.label}</Stamp>
      <h2 className="mt-2 font-display text-2xl">Plain ranking against KaamSetu</h2>
      <p className="text-sm text-ink/70">{report.disclaimer}</p>
      <p className="text-xs text-ink/50">
        {report.seekers} seekers · {report.jobs} cleared jobs · 4 simulated weeks. This does not rewrite live profiles.
      </p>
      <div className="mt-3 space-y-3">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="text-sm font-semibold">{row.label}</div>
            <Bar label="Ranking" value={row.rank} max={row.percent ? 1 : Math.max(row.rank, row.fair, 0.01)} percent={row.percent} tone="bg-ink/40" />
            <Bar label="KaamSetu" value={row.fair} max={row.percent ? 1 : Math.max(row.rank, row.fair, 0.01)} percent={row.percent} tone="bg-green" />
          </div>
        ))}
      </div>
      <ul className="mt-4 space-y-1 text-sm text-ink/80">
        {report.read.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </section>
  );
}

function Bar({ label, value, max, percent, tone }: { label: string; value: number; max: number; percent?: boolean; tone: string }) {
  const width = Math.max(2, Math.min(100, (value / max) * 100));
  const text = percent ? `${Math.round(value * 100)}%` : value.toFixed(2);
  return (
    <div className="mt-1 grid grid-cols-[88px_1fr_48px] items-center gap-2 text-xs">
      <span>{label}</span>
      <span className="h-2 rounded-full bg-ink/10">
        <span className={`block h-2 rounded-full ${tone}`} style={{ width: `${width}%` }} />
      </span>
      <span className="text-right">{text}</span>
    </div>
  );
}
