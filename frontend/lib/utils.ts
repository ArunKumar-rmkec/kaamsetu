import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function inr(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function listen(lang: string, onText: (text: string) => void) {
  const host = window as Window & {
    SpeechRecognition?: new () => SpeechRec;
    webkitSpeechRecognition?: new () => SpeechRec;
  };
  const Rec = host.SpeechRecognition || host.webkitSpeechRecognition;
  if (!Rec) return false;
  const rec = new Rec();
  rec.lang = lang === "ta" ? "ta-IN" : "en-IN";
  rec.onresult = (event) => {
    const text = event.results?.[0]?.[0]?.transcript;
    if (text) onText(text);
  };
  rec.start();
  return true;
}

type SpeechRec = {
  lang: string;
  start: () => void;
  onresult: ((event: { results: { 0: { 0: { transcript: string } } } }) => void) | null;
};
