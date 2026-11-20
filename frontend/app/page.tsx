"use client";

import { LangToggle } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { useApp } from "@/lib/i18n";
import { Briefcase, Landmark, UserRound } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  const { t } = useApp();
  const roles = [
    { href: "/login?role=seeker", title: t("seeker"), icon: UserRound, copy: "Skills, a workplace you can live with, and a score that explains itself." },
    { href: "/login?role=employer", title: t("employer"), icon: Briefcase, copy: "A checked listing, anonymous candidates, and a hire you can rate later." },
    { href: "/login?role=official", title: t("official"), icon: Landmark, copy: "Exposure, first jobs, and a four-week comparison against plain ranking." },
  ];
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-green">Tech4Bharat · 8.2</p>
          <h1 className="mt-2 font-display text-5xl leading-none text-ink">{t("app")}</h1>
        </div>
        <LangToggle />
      </div>
      <p className="max-w-xl text-lg leading-snug text-ink/80">{t("tagline")}</p>
      <p className="mt-3 max-w-xl text-sm text-ink/60">
        Mock OTP is 123456. Nothing here calls Aadhaar, GST, or a real employer. The district is synthetic Tamil Nadu data.
      </p>
      <div className="mt-8 grid gap-3">
        {roles.map((role) => (
          <Link key={role.href} href={role.href} className="rounded-3xl border border-line bg-card p-4 shadow-ticket">
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-green text-paper">
                <role.icon className="h-6 w-6" />
              </span>
              <div>
                <div className="font-display text-2xl leading-none">{role.title}</div>
                <p className="mt-1 text-sm text-ink/70">{role.copy}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className="mt-6">
        <Button asChild variant="outline">
          <Link href="/login?role=seeker">{t("signIn")}</Link>
        </Button>
      </div>
    </div>
  );
}
