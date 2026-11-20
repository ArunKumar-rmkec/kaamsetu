"use client";

import { Shell } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useApp } from "@/lib/i18n";
import { listen } from "@/lib/utils";
import { Mic } from "lucide-react";
import { useEffect, useState } from "react";

type Turn = { from: "you" | "kaam"; text: string };

export default function ChatPage() {
  const { t, lang } = useApp();
  const [text, setText] = useState("");
  const [turns, setTurns] = useState<Turn[]>([
    {
      from: "kaam",
      text:
        lang === "ta"
          ? "நீங்கள் செய்யும் வேலையை எளிய வார்த்தைகளில் சொல்லுங்கள்."
          : "Tell me the work you can do, in plain words. I will map it to a skill code. I will not invent a job.",
    },
  ]);
  const [voice, setVoice] = useState(false);

  useEffect(() => {
    const host = window as Window & { webkitSpeechRecognition?: unknown; SpeechRecognition?: unknown };
    setVoice(Boolean(host.webkitSpeechRecognition || host.SpeechRecognition));
  }, []);

  async function send(message: string) {
    const clean = message.trim();
    if (!clean) return;
    setTurns((current) => [...current, { from: "you", text: clean }]);
    setText("");
    const result = await api<{ reply: string; mapped_skills: { title_en: string; title_ta: string; code: string }[] }>(
      "/api/agents/intake",
      { method: "POST", body: { message: clean, lang } },
    );
    const extra = result.mapped_skills?.length
      ? ` (${result.mapped_skills.map((item) => (lang === "ta" ? item.title_ta : item.title_en)).join(", ")})`
      : "";
    setTurns((current) => [...current, { from: "kaam", text: `${result.reply}${extra}` }]);
  }

  const nav = [
    { href: "/seeker", label: t("matches") },
    { href: "/seeker/profile", label: t("profile") },
    { href: "/seeker/week", label: t("week") },
    { href: "/seeker/chat", label: t("chat") },
  ];

  return (
    <Shell nav={nav} role="seeker">
      <h1 className="font-display text-4xl">{t("chat")}</h1>
      <p className="text-sm text-ink/60">Text is enough. Voice uses the browser speech API when the device has it.</p>
      <div className="mt-4 space-y-2">
        {turns.map((turn, index) => (
          <div key={index} className={turn.from === "you" ? "ml-8 rounded-3xl bg-green px-4 py-3 text-paper" : "mr-8 rounded-3xl border border-line bg-card px-4 py-3"}>
            {turn.text}
          </div>
        ))}
      </div>
      <Textarea className="mt-4" value={text} onChange={(event) => setText(event.target.value)} />
      <div className="mt-2 flex gap-2">
        <Button onClick={() => send(text)}>{t("submit")}</Button>
        {voice ? (
          <Button variant="outline" onClick={() => listen(lang, (heard) => send(heard))}>
            <Mic className="h-4 w-4" />
            Voice
          </Button>
        ) : null}
      </div>
    </Shell>
  );
}
