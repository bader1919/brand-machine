# BYMB Brand Machine — Reports

AI-generated brand identity reports from the BYMB Brand Machine pipeline.

## Structure

```
reports/          ← Markdown brand reports (auto-generated from master.json)
scripts/          ← Converter tools
.github/workflows ← GitHub Actions for automated conversion
```

## How it works

1. Brand Machine runs in n8n → generates `master.json` → saves to MinIO/S3
2. GitHub Action fetches `master.json` from `s3.bymb.bh`
3. `json_to_md.py` converts it to clean markdown
4. Report is committed to `reports/` folder

## Manual trigger

Go to **Actions** → **Brand Report — JSON to Markdown** → **Run workflow** → enter the report slug.

## From n8n (automatic)

Add an HTTP Request node that calls:
```
POST https://api.github.com/repos/bader1919/brand-machine/dispatches
Authorization: Bearer YOUR_GITHUB_TOKEN
Body: { "event_type": "brand-report-ready", "client_payload": { "report_slug": "bymb-2026-03-14-1656" } }
```

---

*BYMB Consultancy Services · by-mb.com*
