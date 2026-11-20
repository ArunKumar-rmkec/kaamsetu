"use client";

import { Band, DistrictText, Notice, Reasons, Shell, Stamp } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { EmployerMe } from "@/lib/types";
import { inr } from "@/lib/utils";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function EmployerHome() {
  const { t } = useApp();
  const [me, setMe] = useState<EmployerMe | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<EmployerMe>("/api/employers/me")
      .then(setMe)
      .catch((err) => setError(err.message));
  }, []);

  const nav = [
    { href: "/employer", label: t("jobs") },
    { href: "/employer/verify", label: t("trust") },
    { href: "/employer/jobs/new", label: t("postJob") },
    { href: "/employer/hires", label: t("hires") },
  ];

  return (
    <Shell nav={nav} role="employer">
      {error ? <Notice>{error}</Notice> : null}
      {me ? (
        <>
          <Stamp>{me.verification_label}</Stamp>
          <h1 className="mt-2 font-display text-4xl leading-none">{me.company_name}</h1>
          <p className="mt-1 text-sm text-ink/60">
            <DistrictText id={me.district_id} />
          </p>
          <div className="mt-4 flex items-end justify-between rounded-3xl border border-line bg-card p-4">
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-ink/50">{t("trustScore")}</div>
              <div className="font-display text-5xl leading-none">{Math.round(me.trust_score)}</div>
            </div>
            <Band band={me.trust_band} />
          </div>
          <div className="mt-3">
            <Reasons items={me.trust_reasons} />
          </div>
          {!me.verified ? (
            <Link href="/employer/verify" className="mt-4 block rounded-3xl bg-clay p-4 text-paper">
              Finish the simulated API Setu checks before a listing can reach seekers.
            </Link>
          ) : null}
          <div className="mt-6 flex items-center justify-between">
            <h2 className="font-display text-2xl">{t("jobs")}</h2>
            <Button asChild size="sm">
              <Link href="/employer/jobs/new">{t("postJob")}</Link>
            </Button>
          </div>
          <div className="mt-3 space-y-3">
            {me.jobs.map((job) => (
              <Link key={job.id} href={`/employer/jobs/${job.id}`} className="block rounded-3xl border border-line bg-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-display text-2xl leading-none">{job.title}</div>
                    <p className="mt-1 text-sm text-ink/60">
                      {inr(job.salary_min)}–{inr(job.salary_max)} · {job.filled}/{job.openings} hired
                    </p>
                  </div>
                  <span className={job.verification_status === "passed" ? "text-xs font-bold text-green" : "text-xs font-bold text-clay"}>
                    {job.verification_status}
                  </span>
                </div>
                <p className="mt-2 text-xs uppercase tracking-wide text-ink/40">{job.verification_source}</p>
              </Link>
            ))}
          </div>
        </>
      ) : (
        <p>Loading the workplace…</p>
      )}
    </Shell>
  );
}
