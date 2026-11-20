export type Lang = "en" | "ta";

export type Reason = { code: string; en: string; ta: string };

export type District = { id: string; name_en: string; name_ta: string; lat: number; lng: number };

export type SkillMeta = { code: string; title_en: string; title_ta: string; sector: string };

export type Question = { id: string; prompt_en: string; prompt_ta: string };

export type Meta = {
  districts: District[];
  taxonomy: SkillMeta[];
  sectors: { id: string; en: string; ta: string }[];
  questions: Question[];
  otp_hint: string;
};

export type SessionUser = { id: number; name: string; phone: string; role: "seeker" | "employer" | "official" };

export type Badge = { code: string; en: string; ta: string };

export type SeekerMe = {
  user: SessionUser;
  clock: { week: number; day: number; label: string };
  skills: { code: string; level: number; title_en: string; title_ta: string }[];
  answers: { question_id: string; answer: string; rubric_score: number }[];
  profile: {
    district_id: string;
    education: string;
    gender: string;
    age: number;
    years_experience: number;
    expected_wage: number;
    shift: string;
    night_ok: boolean;
    physical: number;
    setting: string;
    lodging_needed: boolean;
    max_commute_km: number;
    supervision: string;
    team_size: string;
    consent: boolean;
    onboarding_complete: boolean;
    skill_mu: number;
    skill_rd: number;
    skill_index: number;
    skill_band: string;
    potential: number;
    potential_velocity: number;
    potential_band: string;
    exposure: number;
    checkin_streak: number;
    badges: Badge[];
    reasons: { skill: Reason[]; potential: Reason[] };
    photo: string;
  };
};

export type MatchCard = {
  match_id: number;
  status: string;
  title: string;
  company: string;
  district_id: string;
  salary_min: number;
  salary_max: number;
  will_train: boolean;
  open_to_freshers: boolean;
  shift: string;
  setting: string;
  night_required: boolean;
  lodging_provided: boolean;
  team_size: string;
  distance_km: number;
  fits: { skill: number; environment: number; pay: number; reliability: number; relevance: number; final: number };
  reasons: Reason[];
  identity_shared: boolean;
};

export type Candidate = {
  match_id: number;
  status: string;
  revealed: boolean;
  candidate_ref: string;
  district_id: string;
  age_band: string;
  education: string;
  skills: { code: string; level: number; title_en: string; title_ta: string }[];
  skill_band: string;
  potential_band: string;
  fits: MatchCard["fits"];
  reasons: Reason[];
  distance_km: number;
  name?: string;
  phone?: string;
  age?: number;
};

export type JobCard = {
  id: number;
  title: string;
  sector: string;
  district_id: string;
  salary_min: number;
  salary_max: number;
  will_train: boolean;
  open_to_freshers: boolean;
  openings: number;
  filled: number;
  verification_status: string;
  verification_source: string;
  verification_report: { summary_en?: string; summary_ta?: string; mismatches?: { field: string }[]; label?: string };
  shift: string;
  setting: string;
  night_required: boolean;
  lodging_provided: boolean;
  physical: number;
  team_size: string;
  supervision: string;
  hike_pct: number;
  perks: string;
  skills: { code: string; min_level: number; required: boolean }[];
};

export type EmployerMe = {
  user: SessionUser;
  company_name: string;
  district_id: string;
  verified: boolean;
  trust_score: number;
  trust_band: string;
  trust_reasons: Reason[];
  verification: Record<string, { passed?: boolean; status?: string; masked?: string; value?: string }>;
  verification_label: string;
  jobs: JobCard[];
  clock: { week: number; day: number };
};

export type HireRow = {
  id: number;
  week_hired: number;
  job_title: string;
  company: string;
  seeker_name: string;
  feedback: { week: number; author_role: string; revealed: boolean; rating?: number; comment?: string; hidden?: boolean }[];
};
