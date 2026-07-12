# 🛠️ GitHub Profile README — Setup Guide

Follow these steps to get everything (including the animated snake) working.

---

## 1. Create your profile repository

Your README only shows on your profile if it lives in a **special repo named exactly after your username**.

- Repo name: **`Anup-Ojha`** (must match your username exactly)
- Make it **Public**
- Check **"Add a README file"** when creating it

If you already have this repo, skip to step 2.

---

## 2. Add the files

Place these in the repo with this exact structure:

```
Anup-Ojha/
├── README.md
└── .github/
    └── workflows/
        └── snake.yml
```

- `README.md` → root of the repo
- `snake.yml` → inside `.github/workflows/` (create these folders if they don't exist)

The folder path `.github/workflows/` is **required** — GitHub only runs Actions from there.

---

## 3. Enable the snake animation

The snake image in your README points to a branch that doesn't exist yet. The Action creates it.

1. Push your files to the repo.
2. Go to the **Actions** tab in your repo.
3. If Actions are disabled, click **"I understand my workflows, enable them"**.
4. Find **"Generate Snake Animation"** in the left sidebar → click **"Run workflow"** → **Run**.
5. Wait ~1 minute. This creates an `output` branch containing the snake SVG.

After the first successful run, the snake image in your README will load. It then auto-updates every 12 hours.

### If the workflow fails with a permissions error:
1. Go to **Settings → Actions → General**.
2. Scroll to **"Workflow permissions"**.
3. Select **"Read and write permissions"** → Save.
4. Re-run the workflow.

---

## 4. Verify the other widgets

Most images work instantly, but note:

- **Streak stats** (`streak-stats.herokuapp.com`) occasionally goes down. If it breaks, replace that host in the README with:
  `https://streak-stats.demolab.com/?user=Anup-Ojha&theme=tokyonight&hide_border=false`
- **Profile view counter** starts at 0 and climbs as people visit.

---

## 5. (Optional) Change the theme

Every stat card uses `theme=tokyonight`. To switch the whole look, find-and-replace `tokyonight` in the README with any of:
`radical`, `dracula`, `catppuccin_mocha`, `github_dark`, `gruvbox`, `nord`.

The activity graph uses `theme=tokyo-night` (note the hyphen) and the snake uses its own palette in `snake.yml`.

---

That's it. Once step 3 completes, your profile is fully live. 🎉
