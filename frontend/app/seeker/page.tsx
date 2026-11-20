"use client";

import { DistrictText, FitBar, Notice, Reasons, Shell, Stamp, StatusBadge } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import type { MatchCard, SeekerMe } from "@/lib/types";
import { inr } from "@/lib/utils";
import { Bus, Moon, Sun, Users } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function SeekerMatches() {
  const { t } = useApp();
  const [me, setMe] = useState<SeekerMe | null>(null);
  const [matches, setMatches] = useState<MatchCard[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  async function load() {
    try {
      const [profile, list] = await Promise.all([
        api<SeekerMe>("/api/seekers/me"),
        api<{ matches: MatchCard[] }>("/api/seekers/matches"),
      ]);
      setMe(profile);
      setMatches(list.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load matches");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(id: number, action: "accept" | "decline") {
    setBusy(id);
    try {
      await api(`/api/seekers/matches/${id}/${action}`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update");
    } finally {
      setBusy(null);
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
      <div className="mb-4 flex items-end justify-between">
        <div>
          <Stamp>{me?.clock.label ?? t("simulated")}</Stamp>
          <h1 className="mt-2 font-display text-4xl">{me ? me.user.name.split(" ")[0] : t("matches")}</h1>
          {me ? (
            <p className="text-sm text-ink/60">
              Week {me.clock.week} · Day {me.clock.day}
            </p>
          ) : null}
        </div>
      </div>
      {error ? <Notice>{error}</Notice> : null}
      {me && !me.profile.onboarding_complete ? (
        <Link href="/seeker/onboarding" className="mb-4 block rounded-3xl bg-green p-4 text-paper">
          <div className="font-display text-2xl">{t("onboard")}</div>
          <p className="text-sm text-paper/80">Skills, the workplace you want, and six short answers.</p>
        </Link>
      ) : null}
      {!matches.length && me?.profile.onboarding_complete ? <p className="text-sm text-ink/70">{t("emptyMatches")}</p> : null}
      <div className="space-y-3">
        {matches.map((match) => (
          <article key={match.match_id} className="rounded-3xl border border-line bg-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-2xl leading-none">{match.title}</h2>
                <p className="mt-1 text-sm text-ink/70">
                  {match.company} · <DistrictText id={match.district_id} />
                </p>
              </div>
              <StatusBadge status={match.status} />
            </div>
            <p className="mt-3 font-display text-xl">
              {inr(match.salary_min)}–{inr(match.salary_max)}
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-1 rounded-full bg-paper px-2 py-1">
                {match.shift === "night" ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
                {match.shift}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-paper px-2 py-1">
                <Bus className="h-3.5 w-3.5" />
                {match.distance_km} km
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-paper px-2 py-1">
                <Users className="h-3.5 w-3.5" />
                {match.team_size}
              </span>
              {match.will_train ? <span className="rounded-full bg-green/10 px-2 py-1 text-green">{t("train")}</span> : null}
              {match.lodging_provided ? <span className="rounded-full bg-paper px-2 py-1">{t("lodging")}</span> : null}
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3">
              <FitBar label="Skill" value={match.fits.skill} />
              <FitBar label="Place" value={match.fits.environment} />
              <FitBar label="Pay" value={match.fits.pay} />
            </div>
            <div className="mt-3">
              <Reasons items={match.reasons} />
            </div>
            {match.identity_shared ? <p className="mt-3 text-sm font-semibold text-green">Your name and phone are visible to this employer.</p> : null}
            {match.status === "interested" ? (
              <div className="mt-3 flex gap-2">
                <Button disabled={busy === match.match_id} onClick={() => act(match.match_id, "accept")}>
                  {t("accept")}
                </Button>
                <Button variant="outline" disabled={busy === match.match_id} onClick={() => act(match.match_id, "decline")}>
                  {t("decline")}
                </Button>
              </div>
            ) : null}
            {match.status === "allocated" ? <p className="mt-3 text-sm text-ink/60">{t("waiting")} — the employer has not asked yet. Your name stays hidden.</p> : null}
          </article>
        ))}
      </div>
    </Shell>
  );
}
