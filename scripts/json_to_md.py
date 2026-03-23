#!/usr/bin/env python3
"""
Convert Brand Machine master.json → Markdown report
Usage: python json_to_md.py <master.json path or S3 URL> [output.md]
"""

import json
import sys
import os
from datetime import datetime

def esc(text):
    if not text: return ''
    return str(text).strip()

def arr(val):
    return val if isinstance(val, list) else []

def obj(val):
    return val if isinstance(val, dict) and '_error' not in val else {}

def render_dict(d, indent=0):
    lines = []
    prefix = '  ' * indent
    if isinstance(d, dict):
        for k, v in d.items():
            label = k.replace('_', ' ').title()
            if isinstance(v, dict):
                lines.append(f'{prefix}**{label}:**')
                lines.append(render_dict(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f'{prefix}**{label}:**')
                for item in v:
                    if isinstance(item, dict):
                        lines.append(render_dict(item, indent + 1))
                    else:
                        lines.append(f'{prefix}- {esc(item)}')
            else:
                lines.append(f'{prefix}**{label}:** {esc(v)}')
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, dict):
                lines.append(render_dict(item, indent))
            else:
                lines.append(f'{prefix}- {esc(item)}')
    return '\n'.join(lines)


def convert(master):
    meta = master.get('meta', {})
    a1 = master.get('agent1_strategy', {}).get('english', master.get('agent1_strategy', {}))
    a1_ar = master.get('agent1_strategy', {}).get('arabic', {})
    a2 = master.get('agent2_market', {}).get('english', master.get('agent2_market', {}))
    a3 = master.get('agent3_visual', {}).get('english', master.get('agent3_visual', {}))
    a4 = master.get('agent4_analysis', {})
    a5 = master.get('agent5_report', {})
    cp = master.get('creative_pack', {})
    imgs = master.get('image_assets', [])

    brand = meta.get('brand_name', 'Brand')
    date = meta.get('run_date', datetime.now().isoformat())[:10]

    md = []

    # HEADER
    md.append(f'# {brand} — Brand Identity Report\n')
    md.append(f'| Field | Value |')
    md.append(f'|-------|-------|')
    md.append(f'| Generated | {date} |')
    md.append(f'| Industry | {esc(meta.get("industry", ""))} |')
    md.append(f'| Market | {esc(meta.get("country", ""))} |')
    md.append(f'| Report ID | `{esc(meta.get("report_slug", ""))}` |')
    if meta.get('live_url'):
        md.append(f'| Live Report | [{meta["live_url"]}]({meta["live_url"]}) |')
    md.append('\n---\n')

    # 01: STRATEGY
    md.append('## 01 — Brand Strategy\n')

    pos = a1.get('positioning_statement', a1.get('positioning', ''))
    if pos:
        md.append('### Positioning Statement\n')
        if isinstance(pos, dict):
            for k, v in pos.items():
                md.append(f'- **{k.replace("_"," ").title()}:** {esc(v)}')
        else:
            md.append(esc(pos))
        md.append('')

    uvp = a1.get('unique_value_proposition', a1.get('uvp', ''))
    if uvp:
        md.append('### Unique Value Proposition\n')
        md.append(esc(uvp if not isinstance(uvp, dict) else uvp.get('statement', str(uvp))))
        md.append('')

    arch = a1.get('brand_archetype', a1.get('archetype', ''))
    if arch:
        md.append('### Brand Archetype\n')
        if isinstance(arch, dict):
            md.append(f'**{esc(arch.get("primary", arch.get("name", "")))}**')
            j = arch.get('justification', arch.get('rationale', ''))
            if j: md.append(f'\n{esc(j)}')
        else:
            md.append(f'**{esc(arch)}**')
        md.append('')

    traits = arr(a1.get('brand_personality_traits', a1.get('personality_traits', [])))
    if traits:
        md.append('### Brand Personality\n')
        for t in traits:
            md.append(f'- {esc(t if not isinstance(t, dict) else t.get("trait", t.get("name", str(t))))}')
        md.append('')

    pillars = arr(a1.get('messaging_pillars', a1.get('pillars', [])))
    if pillars:
        md.append('### Messaging Pillars\n')
        for p in pillars:
            if isinstance(p, dict):
                md.append(f'- **{esc(p.get("name", p.get("pillar", "")))}** — {esc(p.get("description", p.get("detail", "")))}')
            else:
                md.append(f'- {esc(p)}')
        md.append('')

    tone = a1.get('tone_of_voice', a1.get('tone', ''))
    if tone:
        md.append('### Tone of Voice\n')
        md.append(esc(tone if not isinstance(tone, dict) else tone.get('description', str(tone))))
        md.append('')

    md.append('---\n')

    # 02: MARKET
    md.append('## 02 — Market Intelligence\n')

    comps = arr(a2.get('competitor_analysis', a2.get('competitors', a2.get('competitor_pattern_analysis', []))))
    for c in comps:
        if isinstance(c, dict):
            name = c.get('name', c.get('competitor', 'Competitor'))
            md.append(f'### {esc(name)}\n')
            for k, v in c.items():
                if k in ('name', 'competitor'): continue
                md.append(f'- **{k.replace("_"," ").title()}:** {esc(v if not isinstance(v, dict) else str(v))}')
            md.append('')

    md.append('---\n')

    # 03: VISUAL IDENTITY
    md.append('## 03 — Visual Identity\n')

    palette = a3.get('suggested_color_palette_structure', {})
    if obj(palette):
        md.append('### Color Palette\n')
        md.append('| Role | Name | Hex | Usage |')
        md.append('|------|------|-----|-------|')
        for tier in ['primary', 'secondary', 'accent', 'neutral']:
            t = palette.get(tier, {})
            if isinstance(t, dict) and t.get('hex'):
                md.append(f'| {tier.title()} | {esc(t.get("name", tier))} | `{t["hex"]}` | {esc(t.get("role", ""))} |')
        sup = palette.get('supporting_colors', {})
        if obj(sup):
            for k, v in sup.items():
                if isinstance(v, dict) and v.get('hex'):
                    md.append(f'| Supporting | {esc(k.replace("_"," ").title())} | `{v["hex"]}` | {esc(v.get("role", ""))} |')
        status = palette.get('status_colors', {})
        if obj(status):
            for k, v in status.items():
                if isinstance(v, dict) and v.get('hex'):
                    md.append(f'| Status | {esc(k.title())} | `{v["hex"]}` | {esc(v.get("usage", ""))} |')
        md.append('')

    typo = a3.get('typography_direction', {})
    if obj(typo):
        en = typo.get('english', typo)
        md.append('### Typography\n')
        hf = en.get('heading_font', '')
        bf = en.get('body_font', '')
        if hf: md.append(f'- **Heading:** {esc(hf)}')
        if bf: md.append(f'- **Body:** {esc(bf)}')
        rat = en.get('pairing_rationale', '')
        if rat: md.append(f'- **Rationale:** {esc(rat)}')
        md.append('')

    imagery = a3.get('imagery_photography_direction', {})
    if obj(imagery):
        md.append('### Imagery Direction\n')
        mood = imagery.get('mood', '')
        if mood: md.append(f'**Mood:** {esc(mood)}\n')
        approved = arr(imagery.get('approved_imagery', []))
        for a in approved: md.append(f'- ✓ {esc(a)}')
        banned = arr(imagery.get('banned_imagery', []))
        for b in banned: md.append(f'- ✕ {esc(b)}')
        md.append('')

    rules = a3.get('visual_consistency_rules', {})
    if obj(rules):
        nn = arr(rules.get('non_negotiables', []))
        if nn:
            md.append('### Non-Negotiable Rules\n')
            for i, r in enumerate(nn, 1): md.append(f'{i}. {esc(r)}')
            md.append('')

    md.append('---\n')

    # 04: AUDIT
    md.append('## 04 — Audit & Scores\n')

    scores = a4.get('scores', {})
    if scores:
        md.append('| Metric | Score |')
        md.append('|--------|-------|')
        for k, v in scores.items():
            if v or v == 0:
                md.append(f'| {k.replace("_"," ").title()} | {esc(v)} |')
        md.append('')

    md.append('---\n')

    # 05: REPORT
    md.append('## 05 — Executive Report\n')

    report_md = a5.get('full_report_markdown', '')
    if report_md:
        md.append(report_md)
    else:
        md.append('*Report not generated in this run.*')
    md.append('\n---\n')

    # 06: IMAGES
    md.append('## 06 — Generated Images\n')

    if imgs:
        md.append('| # | Type | Aspect | Usage |')
        md.append('|---|------|--------|-------|')
        for i, img in enumerate(imgs):
            md.append(f'| {i+1} | {esc(img.get("asset_type", ""))} | {esc(img.get("aspect_ratio", ""))} | {esc(img.get("usage_context", ""))} |')
        b64 = sum(1 for i in imgs if i.get('image_base64') or i.get('base64'))
        md.append(f'\n*{b64}/{len(imgs)} with base64 data*')
    else:
        md.append('*No images in this run.*')
    md.append('\n---\n')

    md.append(f'*BYMB Brand Machine · {date}*\n')

    return '\n'.join(md)


if __name__ == '__main__':
    import urllib.request

    src = sys.argv[1] if len(sys.argv) > 1 else 'master.json'
    out = sys.argv[2] if len(sys.argv) > 2 else None

    if src.startswith('http'):
        print(f'Fetching: {src}')
        data = urllib.request.urlopen(src).read()
        master = json.loads(data)
    else:
        with open(src) as f:
            master = json.load(f)

    slug = master.get('meta', {}).get('report_slug', 'report')
    if not out:
        out = f'reports/{slug}.md'

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)

    md = convert(master)
    with open(out, 'w') as f:
        f.write(md)

    print(f'Written: {out} ({len(md)} chars)')
