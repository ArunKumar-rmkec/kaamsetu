"use client";

import { Avatar, Band, Notice, Reasons, Shell } from "@/components/bits";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { districtName, useApp } from "@/lib/i18n";
import type { SeekerMe } from "@/lib/types";
import { inr } from "@/lib/utils";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function ProfilePage() {
  const { t, lang, meta } = useApp();
  const [me, setMe] = useState<SeekerMe | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<SeekerMe>("/api/seekers/me")
      .then(setMe)
      .catch((err) => setError(err.message));
  }, []);

  async function toggle(consent: boolean) {
    if (!me) return;
    await api("/api/seekers/consent", { method: "POST", body: { consent } });
    setMe({ ...me, profile: { ...me.profile, consent } });
  }

  const nav = [
    { href: "/seeker", label: t("matches") },
    { href: "/seeker/profile", label: t("profile") },
    { href: "/seeker/week", label: t("week") },
    { href: "/seeker/chat", label: t("chat") },
  ];

  return (
    <Shell nav={nav} role="seeker">
      {error ? <Notice>{error}</Notice> : null}
      {!me ? <p className="text-sm">Loading your profile…</p> : null}
      {me ? (
        <div className="space-y-4">
          <div className="flex gap-4 rounded-3xl border border-line bg-card p-4">
            <Avatar name={me.user.name} />
            <div className="min-w-0 flex-1">
              <h1 className="font-display text-3xl leading-none">{me.user.name}</h1>
              <p className="mt-1 text-sm text-ink/70">
                {districtName(meta, me.profile.district_id, lang)} · {me.profile.education} · {me.profile.age}
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <Score title={t("skillScore")} value={me.profile.skill_index} band={me.profile.skill_band} detail={`μ ${Math.round(me.profile.skill_mu)} · RD ${Math.round(me.profile.skill_rd)}`} />
                <Score title={t("potentialScore")} value={me.profile.potential} band={me.profile.potential_band} detail={`trend ${me.profile.potential_velocity > 0 ? "+" : ""}${me.profile.potential_velocity}`} />
              </div>
            </div>
          </div>
          <section className="rounded-3xl border border-line bg-card p-4">
            <h2 className="font-display text-xl">{t("reasons")}</h2>
            <p className="mt-2 text-xs font-bold uppercase tracking-wider text-green">{t("skillScore")}</p>
            <div className="mt-2">
              <Reasons items={me.profile.reasons.skill} />
            </div>
            <p className="mt-4 text-xs font-bold uppercase tracking-wider text-green">{t("potentialScore")}</p>
            <div className="mt-2">
              <Reasons items={me.profile.reasons.potential} />
            </div>
          </section>
          <section className="rounded-3xl border border-line bg-card p-4">
            <h2 className="font-display text-xl">{t("badges")}</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {me.profile.badges.length ? (
                me.profile.badges.map((badge) => (
                  <Badge key={badge.code} className="bg-marigold/30">
                    {lang === "ta" ? badge.ta : badge.en}
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-ink/60">Badges appear after a profile, a match, check-ins, or a hire.</p>
              )}
            </div>
          </section>
          <section className="rounded-3xl border border-line bg-card p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-xl">{t("skills")}</h2>
              <Button asChild variant="outline" size="sm">
                <Link href="/seeker/onboarding">{t("onboard")}</Link>
              </Button>
            </div>
            <ul className="mt-3 space-y-2">
              {me.skills.map((skill) => (
                <li key={skill.code} className="flex items-center justify-between text-sm">
                  <span>{lang === "ta" ? skill.title_ta : skill.title_en}</span>
                  <span className="font-semibold">
                    {skill.code} · {skill.level}/5
                  </span>
                </li>
              ))}
            </ul>
            <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <Fact k={t("wage")} v={inr(me.profile.expected_wage)} />
              <Fact k={t("shift")} v={me.profile.shift} />
              <Fact k={t("setting")} v={me.profile.setting} />
              <Fact k={t("night")} v={me.profile.night_ok ? "yes" : "no"} />
              <Fact k={t("commute")} v={`${me.profile.max_commute_km} km`} />
              <Fact k={t("lodging")} v={me.profile.lodging_needed ? "needed" : "no"} />
              <Fact k={t("physical")} v={String(me.profile.physical)} />
              <Fact k={t("team")} v={me.profile.team_size} />
            </dl>
          </section>
          <section className="flex items-center justify-between rounded-3xl border border-line bg-card p-4">
            <div>
              <h2 className="font-display text-xl">{t("consent")}</h2>
              <p className="text-sm text-ink/60">Off means you drop out of the next allocation. A hire already shared stays shared.</p>
            </div>
            <Switch checked={me.profile.consent} onCheckedChange={toggle} aria-label={t("consent")} />
          </section>
        </div>
      ) : null}
    </Shell>
  );
}

function Score({ title, value, band, detail }: { title: string; value: number; band: string; detail: string }) {
  return (
    <div className="rounded-2xl bg-paper p-2">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-ink/60">{title}</div>
      <div className="flex items-end justify-between gap-1">
        <span className="font-display text-3xl leading-none">{Math.round(value)}</span>
        <Band band={band} />
      </div>
      <div className="mt-1 text-[11px] text-ink/50">{detail}</div>
    </div>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-2xl bg-paper px-3 py-2">
      <dt className="text-[11px] uppercase tracking-wide text-ink/50">{k}</dt>
      <dd className="font-semibold">{v}</dd>
    </div>
  );
}
