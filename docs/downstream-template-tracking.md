# Tracking micro-saas-template in downstream projects

Every product repo bootstrapped from **micro-saas-template** (MST) must track which template commit it was based on, so you can inspect and port upstream changes later.

Use the same convention as [family-activity-finder](https://github.com/wlatanowicz/family-activity-finder): a **`docs/micro-saas-template-origin.md`** file plus a README link.

## What to add in each downstream repo

### 1. `docs/micro-saas-template-origin.md`

Create this file when you bootstrap a new product. Fill in the bootstrap commit from your MST clone at fork/copy time:

```markdown
# micro-saas-template origin

This project was bootstrapped from [micro-saas-template](https://github.com/wlatanowicz/micro-saas-template).

| Field | Value |
|-------|-------|
| Template repository | `git@github.com:wlatanowicz/micro-saas-template.git` |
| Commit (bootstrap) | `<full-sha-at-bootstrap>` |
| Commit date | YYYY-MM-DD |
| Commit message | `<subject line of bootstrap commit>` |
| Applied to this repo | YYYY-MM-DD |

## Applying future template updates

1. In a clone of `micro-saas-template`, inspect changes since the bootstrap commit:

   ```bash
   git log <bootstrap-sha>..HEAD --oneline
   git diff <bootstrap-sha>..HEAD
   ```

2. Cherry-pick or manually port relevant changes into this repo. Skip product-specific files (e.g. product discovery docs, i18n product strings, `serverless.yml` `service:` name).

3. After merging template changes, update the **Commit (bootstrap)** row above to the new baseline commit and set **Applied to this repo** to today's date.
```

Replace `<bootstrap-sha>` in the bash examples with the actual SHA from the table (as in family-activity-finder).

### 2. README link

In the repo README **Layout** (or equivalent) section, mention the origin doc, for example:

```markdown
- `docs/` — … and [micro-saas-template origin](docs/micro-saas-template-origin.md) (tracked commit for future template updates)
```

## Workflow summary

| Step | Action |
|------|--------|
| Bootstrap | Record MST commit SHA, date, and message in `docs/micro-saas-template-origin.md` |
| Ongoing | When MST changes, `git log` / `git diff` from tracked SHA to `HEAD` in an MST clone |
| Port | Cherry-pick or manually merge relevant template changes; skip product-specific files |
| After merge | Bump **Commit (bootstrap)** to the new MST baseline; set **Applied to this repo** to today |

## Reference implementation

See [family-activity-finder/docs/micro-saas-template-origin.md](https://github.com/wlatanowicz/family-activity-finder/blob/main/docs/micro-saas-template-origin.md) and its README layout section.
