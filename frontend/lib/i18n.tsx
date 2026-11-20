"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Lang, Meta, SessionUser } from "./types";

const copy = {
  en: {
    app: "KaamSetu",
    tagline: "A bridge from a young person's skills to a workplace that can actually keep them.",
    seeker: "Job seeker",
    employer: "Employer",
    official: "District desk",
    signIn: "Sign in",
    phone: "Mobile number",
    name: "Your name",
    otp: "OTP",
    sendOtp: "Send mock OTP",
    verify: "Continue",
    company: "Workplace name",
    district: "District",
    matches: "Matches",
    profile: "Profile",
    week: "This week",
    chat: "Talk",
    jobs: "Jobs",
    postJob: "Post a job",
    trust: "Trust",
    hires: "Hires",
    candidates: "Candidates",
    consent: "Share my details only after I accept",
    skillScore: "Skill Score",
    potentialScore: "Potential Score",
    trustScore: "Employer Trust",
    high: "High",
    medium: "Medium",
    building: "Building",
    badges: "Badges",
    reasons: "Why this band",
    checkIn: "Daily check-in",
    feedback: "Checkpoint",
    accept: "Accept and share my details",
    decline: "Not this one",
    interest: "Send interest",
    hire: "Mark hired",
    waiting: "Waiting",
    simulate: "Simulate 4 weeks",
    advanceDay: "Advance 1 day",
    advanceWeek: "Advance 1 week",
    runMatch: "Run matching",
    flagged: "Flagged listings",
    fairness: "District fairness",
    next: "Next",
    back: "Back",
    save: "Save profile",
    skills: "Skills",
    workplace: "Workplace",
    questions: "Six questions",
    shift: "Shift",
    night: "Night work",
    physical: "Physical intensity",
    setting: "Indoor / outdoor",
    lodging: "Lodging",
    commute: "Max commute (km)",
    supervision: "Supervision",
    team: "Team size",
    wage: "Expected monthly wage",
    salary: "Monthly salary",
    hike: "Hike %",
    perks: "Perks",
    negotiate: "Negotiation range",
    freshers: "Open to freshers",
    train: "Will train",
    openings: "Openings",
    video: "Workplace video",
    mismatch: "Demo: video should disagree with the job",
    simulated: "SIMULATED",
    language: "தமிழ்",
    home: "Home",
    verifyBiz: "Government checks",
    emptyMatches: "No openings in your sector yet. A district run will fill this.",
    emptyHires: "No hire recorded yet.",
    moodGood: "Good day",
    moodOkay: "Okay",
    moodTough: "Tough day",
    note: "Note",
    submit: "Submit",
    revealed: "Both sides are visible",
    hidden: "Hidden until they reply",
    photo: "Photo not taken",
    education: "Education",
    age: "Age",
    experience: "Years of work",
    gender: "Gender",
    map: "Map my words",
    level: "Level",
    required: "Required",
    samplePass: "Fill a passing sample",
    sampleFail: "Fill a failing sample",
    logout: "Sign out",
    onboard: "Build your profile",
    exposure: "Times recommended",
    relevance: "Match",
    blind: "Your rating stays hidden until the other side files the same week.",
  },
  ta: {
    app: "காம்சேது",
    tagline: "ஒரு இளைஞரின் திறனையும், அவரைத் தக்கவைக்கும் பணிமனையையும் இணைக்கும் பாலம்.",
    seeker: "வேலை தேடுபவர்",
    employer: "முதலாளி",
    official: "மாவட்ட மேசை",
    signIn: "நுழை",
    phone: "கைபேசி எண்",
    name: "பெயர்",
    otp: "OTP",
    sendOtp: "மாதிரி OTP அனுப்பு",
    verify: "தொடர்க",
    company: "பணிமனை பெயர்",
    district: "மாவட்டம்",
    matches: "பொருத்தங்கள்",
    profile: "சுயவிவரம்",
    week: "இந்த வாரம்",
    chat: "பேசு",
    jobs: "வேலைகள்",
    postJob: "வேலை பதிவு",
    trust: "நம்பிக்கை",
    hires: "பணியமர்த்தல்",
    candidates: "விண்ணப்பதாரர்கள்",
    consent: "நான் ஒப்புக்கொண்ட பிறகே என் விவரங்களைப் பகிரவும்",
    skillScore: "திறன் மதிப்பெண்",
    potentialScore: "ஆற்றல் மதிப்பெண்",
    trustScore: "முதலாளி நம்பிக்கை",
    high: "உயர்",
    medium: "நடுத்தர",
    building: "வளர்கிறது",
    badges: "பதக்கங்கள்",
    reasons: "இந்த பட்டை ஏன்",
    checkIn: "தினசரி பதிவு",
    feedback: "வாரக் கருத்து",
    accept: "ஒப்புக்கொண்டு விவரங்களைப் பகிர்",
    decline: "இது வேண்டாம்",
    interest: "ஆர்வம் தெரிவி",
    hire: "பணியமர்த்தல்",
    waiting: "காத்திருப்பு",
    simulate: "4 வார உருவகம்",
    advanceDay: "1 நாள் முன் நகர்த்து",
    advanceWeek: "1 வாரம் முன் நகர்த்து",
    runMatch: "பொருத்தம் இயக்கு",
    flagged: "குறிக்கப்பட்ட பட்டியல்",
    fairness: "மாவட்ட நியாயம்",
    next: "அடுத்து",
    back: "பின்",
    save: "சுயவிவரத்தை சேமி",
    skills: "திறன்கள்",
    workplace: "பணிச்சூழல்",
    questions: "ஆறு கேள்விகள்",
    shift: "ஷிப்ட்",
    night: "இரவு பணி",
    physical: "உடல் உழைப்பு",
    setting: "உள் / வெளி",
    lodging: "தங்கும் இடம்",
    commute: "அதிகபட்ச பயணம் (கி.மீ)",
    supervision: "மேற்பார்வை",
    team: "குழு அளவு",
    wage: "எதிர்பார்க்கும் மாத ஊதியம்",
    salary: "மாத ஊதியம்",
    hike: "உயர்வு %",
    perks: "சலுகைகள்",
    negotiate: "பேச்சுவார்த்தை வரம்பு",
    freshers: "புதியவர்களை ஏற்பேன்",
    train: "பயிற்சி தருவேன்",
    openings: "காலி இடங்கள்",
    video: "பணிமனை காணொலி",
    mismatch: "மாதிரி: காணொலி வேலை விவரத்துடன் முரண்பட வேண்டும்",
    simulated: "உருவகம்",
    language: "English",
    home: "முகப்பு",
    verifyBiz: "அரசு சரிபார்ப்பு",
    emptyMatches: "உங்கள் பகுதியில் இன்னும் வேலை இல்லை.",
    emptyHires: "பணியமர்த்தல் இன்னும் இல்லை.",
    moodGood: "நல்ல நாள்",
    moodOkay: "சரி",
    moodTough: "கடின நாள்",
    note: "குறிப்பு",
    submit: "சமர்ப்பி",
    revealed: "இருவரின் கருத்தும் தெரியும்",
    hidden: "அவர்கள் பதிலளிக்கும் வரை மறைவு",
    photo: "புகைப்படம் இல்லை",
    education: "கல்வி",
    age: "வயது",
    experience: "பணி ஆண்டுகள்",
    gender: "பாலினம்",
    map: "சொற்களை பொருத்து",
    level: "நிலை",
    required: "கட்டாயம்",
    samplePass: "தேர்ச்சி மாதிரி",
    sampleFail: "தோல்வி மாதிரி",
    logout: "வெளியேறு",
    onboard: "சுயவிவரத்தை உருவாக்கு",
    exposure: "பரிந்துரைகள்",
    relevance: "பொருத்தம்",
    blind: "மறுபக்கம் அதே வாரக் கருத்தை தரும் வரை உங்கள் மதிப்பெண் மறைவாக இருக்கும்.",
  },
} as const;

export type CopyKey = keyof (typeof copy)["en"];

type AppState = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: CopyKey) => string;
  user: SessionUser | null;
  setUser: (user: SessionUser | null) => void;
  meta: Meta | null;
  ready: boolean;
};

const Ctx = createContext<AppState | null>(null);

export function Providers({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [user, setUserState] = useState<SessionUser | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("ks_lang");
    if (stored === "ta" || stored === "en") setLangState(stored);
    const raw = localStorage.getItem("ks_user");
    if (raw) {
      try {
        setUserState(JSON.parse(raw) as SessionUser);
      } catch {
        localStorage.removeItem("ks_user");
      }
    }
    api<Meta>("/api/meta")
      .then(setMeta)
      .catch(() => setMeta(null))
      .finally(() => setReady(true));
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    }
  }, []);

  const value = useMemo<AppState>(() => {
    return {
      lang,
      setLang: (next) => {
        localStorage.setItem("ks_lang", next);
        setLangState(next);
      },
      t: (key) => copy[lang][key],
      user,
      setUser: (next) => {
        if (next) localStorage.setItem("ks_user", JSON.stringify(next));
        else {
          localStorage.removeItem("ks_user");
          localStorage.removeItem("ks_token");
        }
        setUserState(next);
      },
      meta,
      ready,
    };
  }, [lang, user, meta, ready]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp outside Providers");
  return ctx;
}

export function reasonText(reason: { en: string; ta: string }, lang: Lang) {
  return lang === "ta" ? reason.ta : reason.en;
}

export function districtName(meta: Meta | null, id: string, lang: Lang) {
  const row = meta?.districts.find((item) => item.id === id);
  if (!row) return id;
  return lang === "ta" ? row.name_ta : row.name_en;
}
