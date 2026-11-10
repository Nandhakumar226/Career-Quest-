# Career Quest — Personal Job Search Command Center

A self-contained, local-first career dashboard for project management, PMO, implementation, delivery and equivalent roles. It starts with **no sample jobs or applications**. Listings only appear after a configured public source returns them or you add a job manually.

## Files

- `index.html` — responsive seven-tab dashboard; vanilla HTML/CSS/JS.
- `fetch_jobs.py` — Python standard-library fetcher; writes `jobs.json`.
- `.github/workflows/fetch.yml` — scheduled and manual GitHub Actions workflow.
- `company_sources.json` — optional company ATS registry (create from the example below).
- `jobs.json` — generated public feed; initially may be absent/empty.

## Features

Today, Kanban pipeline, searchable/filterable jobs, international country planning, skill-gap discovery from saved descriptions, interview answer notes, actual application analytics, editable profile, source health, local JSON backup/import, responsive layout, light/dark theme and reduced-motion-aware original cartoon artwork.

Personal application notes, contacts, interview answers, profile and preferences stay in this browser's `localStorage`. Only public job listings are written to `jobs.json`. Never put API credentials in the frontend, localStorage or committed files.

## Run locally

From this folder:

```bash
python -m http.server 8000
```

Open <http://localhost:8000>. Do not open `index.html` using `file://`: browser fetch of `jobs.json` needs HTTP. Without a feed, the dashboard still works for manual job entry.

## Configure Adzuna

1. Register for API access at <https://developer.adzuna.com/>.
2. Create an app and obtain an application ID and key.
3. Locally, set environment variables (do not paste secrets into code):

```bash
# macOS/Linux
export ADZUNA_APP_ID="your-id"
export ADZUNA_APP_KEY="your-key"
python fetch_jobs.py
```

```powershell
# Windows PowerShell
$env:ADZUNA_APP_ID="your-id"
$env:ADZUNA_APP_KEY="your-key"
python fetch_jobs.py
```

Adzuna is queried for configured role phrases across supported country codes. Salary conversion to LPA is performed only for India when a numeric salary range is returned. Other country salary data is left unknown in this initial connector.

## Other implemented public connectors

- Remote OK public API
- Remotive public API
- Arbeitnow public API
- Greenhouse public board API (company-specific board slug)
- Lever public postings API (company-specific site slug)

Connectors run independently. A failure from one does not stop the others. Public endpoint availability and provider terms/rate limits can change; review each provider's current terms before use.

### Restricted / pending sources

LinkedIn, Naukri, Indeed, Foundit, Glassdoor and other login-, partner-, credential- or anti-bot-restricted portals are **not scraped**. They are not falsely shown as connected. Add an authorised integration only where you have permission and credentials. Workday, SmartRecruiters, Ashby, Workable, Recruitee, Personio, Teamtailor, Oracle, SAP, Darwinbox and iCIMS do not share one universal public endpoint; support needs the employer's permitted endpoint/API and may require a connector implementation.

## Add company career sources

Create `company_sources.json` beside `fetch_jobs.py`:

```json
[
  {
    "name": "Example Employer",
    "country": "Netherlands",
    "ats": "greenhouse",
    "board": "employer-board-slug"
  },
  {
    "name": "Another Employer",
    "country": "India",
    "ats": "lever",
    "board": "employer-site-slug"
  }
]
```

Use `ats` equal to `greenhouse` or `lever` for the included connectors. The `board` value is the public board/site identifier, not the careers-page URL. Other ATS types are reported as configuration required, not connected. Add/remove entries in this JSON registry without editing the fetch engine. The browser's company registry is a personal planning list; configure actual fetchable boards in `company_sources.json`.

## GitHub Actions every 30 minutes

1. Create a GitHub repository and upload these files, including `.github/workflows/fetch.yml`.
2. In repository **Settings → Secrets and variables → Actions**, add:
   - `ADZUNA_APP_ID`
   - `ADZUNA_APP_KEY`
3. Under **Settings → Actions → General → Workflow permissions**, allow read and write permissions for repository contents (the workflow also requests `contents: write`).
4. Open **Actions → Refresh job feed → Run workflow** to perform the first run.
5. Confirm `jobs.json` is created/updated in the repository.
6. Enable GitHub Pages from **Settings → Pages**, deploying from the `main` branch and repository root.
7. Open the published Pages URL.

GitHub scheduled workflows use UTC and may be delayed by GitHub load; `*/30 * * * *` requests a run every 30 minutes but does not guarantee execution at the exact minute. The browser refresh interval only controls how often this page checks `jobs.json`; changing it does not change the GitHub Actions schedule.

## Filtering and matching notes

Indian feed rules hide jobs below ₹7 LPA when salary is known; Chennai/Bangalore allow Remote and Hybrid; other Indian cities allow Remote only. Unknown salary remains visible. Onsite roles outside target cities and some uncertain work modes may need manual review. International roles are exempt from Indian salary/location filters. The frontend explains hidden reasons and lets you show hidden roles.

Match scoring is deterministic keyword matching against your editable skills and target titles. It is a relevance aid, not an assessment of hiring probability. Missing data stays unknown. Visa sponsorship and international applicant eligibility are not inferred from a listing.

## Data, backup and privacy

- Use **Profile → Export JSON** to download a complete local backup.
- Import validates the basic version and job array before replacing the local state.
- Reset asks for confirmation and keeps a local backup key in this browser.
- Application notes and recruiter contacts never go into `jobs.json`.
- GitHub Pages is public by default. Treat `jobs.json` as public.
- Do not commit private details or API secrets.

## Troubleshooting

- **No feed / fetch error:** confirm the Pages URL and that `jobs.json` exists at the configured path; use browser developer tools for HTTP/JSON errors.
- **Adzuna pending credentials:** add both GitHub Actions secrets and manually rerun the workflow.
- **One source failed:** inspect the `sources` array in `jobs.json` and Actions logs. Other sources continue independently.
- **No results:** broad job-title search phrases may return few results; verify API availability and try again later. No synthetic listings are inserted.
- **Workflow did not run at exact half-hour:** scheduled runs can be delayed; use workflow dispatch for an immediate run.
- **No company ATS jobs:** check the board identifier and public endpoint. An ordinary careers-page URL is not necessarily an API board identifier.
- **Browser doesn't update:** ensure the page is served over HTTP(S), not `file://`, and check the configured jobs JSON URL.

## Known limitations

- No connector can lawfully guarantee access to every job portal. Restricted sites need authorised access.
- The included connectors cover public APIs and selected ATS endpoints only; further ATS integrations need per-employer configuration.
- The browser refresh checks the feed; the GitHub workflow performs collection.
- International visa thresholds, work-life balance scores and sponsorship are intentionally not invented; research and edit country notes using official sources.
- No automated job applications are performed.
- The dashboard has not been validated against every browser/device combination; see the delivered test summary for syntax and smoke checks actually performed.
