"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { districtName, reasonText, useApp } from "@/lib/i18n";
import type { Reason } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Languages } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

export function bandClass(band: string) {
  if (band === "High") return "bg-green text-paper";
  if (band === "Medium") return "bg-marigold text-ink";
  return "bg-clay text-paper";
}

export function Band({ band }: { band: string }) {
  const { t } = useApp();
  const label = band === "High" ? t("high") : band === "Medium" ? t("medium") : t("building");
  return <span className={cn("rounded-full px-2.5 py-1 text-xs font-bold", bandClass(band))}>{label}</span>;
}

export function Stamp({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block -rotate-2 rounded-md border-2 border-clay px-2 py-0.5 text-[11px] font-bold uppercase tracking-widest text-clay">
      {children}
    </span>
  );
}

export function LangToggle() {
  const { lang, setLang, t } = useApp();
  return (
    <Button type="button" variant="outline" size="sm" onClick={() => setLang(lang === "en" ? "ta" : "en")} aria-label="Toggle language">
      <Languages className="h-4 w-4" />
      {t("language")}
    </Button>
  );
}

export function Reasons({ items }: { items: Reason[] }) {
  const { lang } = useApp();
  if (!items?.length) return null;
  return (
    <ol className="space-y-2 text-sm leading-snug text-ink/80">
      {items.slice(0, 3).map((item) => (
        <li key={item.code} className="flex gap-2">
          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-green" />
          <span>{reasonText(item, lang)}</span>
        </li>
      ))}
    </ol>
  );
}

export function FitBar({ label, value }: { label: string; value: number }) {
  const width = Math.max(4, Math.min(100, Math.round(value * 100)));
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-ink/70">
        <span>{label}</span>
        <span>{width}</span>
      </div>
      <div className="h-1.5 rounded-full bg-ink/10">
        <div className="h-1.5 rounded-full bg-green" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function Avatar({ name }: { name: string }) {
  const { t } = useApp();
  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="grid h-20 w-20 place-items-center rounded-full border-2 border-ink bg-marigold font-display text-2xl text-ink">
        {initials || "KS"}
      </div>
      <span className="text-[11px] text-ink/60">{t("photo")}</span>
    </div>
  );
}

export function DistrictText({ id }: { id: string }) {
  const { meta, lang } = useApp();
  return <>{districtName(meta, id, lang)}</>;
}

export function Shell({
  children,
  nav,
  wide = false,
  role,
}: {
  children: React.ReactNode;
  nav: { href: string; label: string }[];
  wide?: boolean;
  role?: string;
}) {
  const { t, user, setUser, ready } = useApp();
  const path = usePathname();
  const router = useRouter();
  useEffect(() => {
    if (!ready) return;
    if (!localStorage.getItem("ks_token")) router.replace(`/login?role=${role ?? "seeker"}`);
  }, [ready, role, router]);
  return (
    <div className={cn("mx-auto min-h-screen w-full pb-24", wide ? "max-w-6xl" : "max-w-3xl")}>
      <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line/80 bg-paper/90 px-4 py-3 backdrop-blur">
        <Link href="/" className="font-display text-xl leading-none">
          {t("app")}
        </Link>
        <div className="flex items-center gap-2">
          <LangToggle />
          {user ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setUser(null);
                router.push("/");
              }}
            >
              {t("logout")}
            </Button>
          ) : null}
        </div>
      </header>
      <main className="px-4 py-5">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-card/95 backdrop-blur">
        <div className={cn("mx-auto flex", wide ? "max-w-6xl" : "max-w-3xl")}>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex-1 px-2 py-3 text-center text-xs font-semibold",
                path === item.href ? "text-green" : "text-ink/60",
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}

export function Notice({ children, tone = "clay" }: { children: React.ReactNode; tone?: "clay" | "green" }) {
  return (
    <div className={cn("rounded-2xl border px-3 py-2 text-sm", tone === "clay" ? "border-clay/40 bg-clay/10" : "border-green/30 bg-green/10")}>
      {children}
    </div>
  );
}

export function Choice({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "min-h-12 rounded-2xl border px-3 text-sm font-semibold",
        active ? "border-green bg-green text-paper" : "border-line bg-card text-ink",
      )}
    >
      {children}
    </button>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge>{status}</Badge>;
}
