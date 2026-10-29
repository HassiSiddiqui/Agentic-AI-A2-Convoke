# What you need for a GitHub repository

Remote: `https://github.com/HassiSiddiqui/Agentic-AI-A2-Convoke.git`

## You need

1. A **GitHub account** (student email is fine).
2. **Git** installed (`git --version` in PowerShell).
3. Permission to create a **new empty repository** (no README on GitHub if we push an existing folder).
4. A decision: **public** (easiest for the teacher/TA) or private with collaborator access.
5. Confirmation that **`.env` will never be committed**. Groq and Gmail secrets stay local.

## Suggested repository name

`A2_23i-2654_Convoke` or `agentic-ai-a2-convoke`

## Commands after you create the empty GitHub repo

Replace `YOURUSER` and `REPO`.

```powershell
cd c:\Uni\agenticai\A2_i232654_HaseebSiddiqui
git init
git add .
git status
git commit -m "Submit Convoke A14 academic event coordinator for Agentic AI Assignment 2."
git branch -M main
git remote add origin https://github.com/YOURUSER/REPO.git
git push -u origin main
```

If GitHub already created a README, pull with `--allow-unrelated-histories` first, or delete that README on the website and push a clean main.

## Do not upload

- `.env`
- Gmail app passwords typed in Streamlit
- `data/store/convoke.sqlite` if it contains a live run you do not want (sample reports are fine)
- `Agentic_AI_assignment-2_Ideas.xlsx` (class workbook, not your deliverable)

`.gitignore` already blocks `.env`, virtualenvs, and `__pycache__`.
