# KaamSetu

A basic, runnable prototype of an agentic job-matching desk for rural youth in Tamil Nadu. Seekers build a skill and workplace profile, employers post a checked listing, and a district allocation spreads recommendations instead of handing the first seats to whoever already ranks highest.

This is a model the team can tune. Scores and the match itself are deterministic code. A language model is used only to phrase or extract, and only when `OPENAI_API_KEY` is set. With no key, every screen still works.

## Run

```bash
chmod +x dev.sh
./dev.sh
```

- Web: http://127.0.0.1:4317
- API: http://127.0.0.1:8421/api/health

`./dev.sh test` runs the scoring and allocation tests. `./dev.sh --reset` rebuilds the synthetic district. Docker is optional (`docker compose up`); the script above is the path this project is run with.

Python 3.12 and Node 22 are enough. The first run creates a virtualenv, installs dependencies, and seeds about 200 seekers and 60 jobs.

## Sign in

The OTP is always `123456`. No SMS is sent.

| Role | Phone | Who |
| --- | --- | --- |
| Seeker | 9840011101 | Priya Selvam, Coimbatore, ITI stitching |
| Employer | 9840022202 | Annamalai Textiles |
| District desk | 9840033303 | Employment office view |

Any other 10-digit number can register. A new seeker walks the onboarding steps; a new employer has to pass the simulated register checks before a job is posted.

## What you can click through

1. Seeker profile: photo placeholder, Skill Score and Potential Score with High / Medium / Building, three reasons, badges, consent.
2. Matches: anonymised until the seeker accepts an employer's interest.
3. Daily check-in and a weekly checkpoint. Ratings stay hidden until both sides file that week.
4. Employer trust, simulated API Setu checks, a structured job plus a workplace video, and candidate cards.
5. District desk: exposure, first-job share, time-to-match, flagged listings, and **Simulate 4 weeks** (plain ranking against the fairness allocation).

The header switches key labels between English and Tamil. Voice input appears when the browser exposes the Web Speech API.

## Where the decisions live

| Decision | Code |
| --- | --- |
| Skill rating | `backend/app/scoring/glicko.py` |
| Potential trend | `backend/app/scoring/kalman.py` |
| Employer trust | `backend/app/scoring/trust.py` |
| Skill / place / pay / reliability | `backend/app/scoring/fit.py` |
| Fairness bonuses | `backend/app/scoring/fairness.py` |
| District allocation | `backend/app/scoring/allocate.py` |
| Agents | `backend/app/agents/` |

`docs/TECHNICAL_REPORT.md` is the internal filing: architecture, every endpoint, the formulas, what is real, and what is mocked. Screenshots are in `docs/screenshots/`.
