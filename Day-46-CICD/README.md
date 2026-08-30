# Day 46 — CI/CD Pipelines with GitHub Actions

> **Phase 6 — DevOps & Infrastructure** | Week 9 | Day 46 of 180

---

## 📌 What I Learned Today

- CI (Continuous Integration): auto-run tests on every push
- CD (Continuous Delivery): auto-deploy passing commits to staging
- GitHub Actions: workflow files live in .github/workflows/
- Workflow structure: name → on → jobs → steps
- `uses`: run a pre-built action from GitHub Marketplace
- `run`: execute a shell command directly
- Triggers: push, pull_request, schedule, workflow_dispatch
- concurrency: cancel-in-progress runs on new push (save minutes)
- needs: job dependency (test only runs after lint passes)
- matrix: test across Python 3.10, 3.11, 3.12 simultaneously
- fail-fast: false — keep running other matrix versions if one fails
- Secrets: Settings → Secrets → reference as ${{ secrets.KEY }}
- Contexts: ${{ github.sha }}, ${{ github.actor }}, ${{ github.ref_name }}
- if: conditionals — run step only on main, only on failure, always()
- cache: pip: built-in pip caching in setup-python action
- actions/upload-artifact: save files between jobs and for download
- actions/github-script: run JavaScript to interact with GitHub API
- Blue-green deployment: deploy to GREEN, test, flip traffic, decommission BLUE
- Rolling deployment: update instances one by one
- Canary deployment: route 5% traffic to new version, monitor, expand
- Branch protection: require CI before merge, no direct pushes to main
- Conventional commits: feat/fix/chore/docs: description format
- cron syntax: "0 9 \* \* 1" = Monday 9am UTC (minute hour dom month dow)
- bandit: static security analysis for Python code
- safety: check dependencies against CVE database
- PR comment automation: actions/github-script creates PR comments
- $GITHUB_OUTPUT: pass values between steps with echo "key=val" >>

## 🔨 Project Built

**Complete CI/CD Pipeline:**

**4 Workflow Files:**

- ci.yml: Lint (ruff) → Test matrix (3 Python versions) → Docker build + health check → Summary
- cd.yml: Staging deploy (simulated) → Smoke tests → Production blue-green deploy → Notification
- security.yml: Safety (CVE scan) + Bandit (static analysis), weekly + on requirements change
- pr_check.yml: PR title convention check + size warning + quick tests + automated PR comment

**Application:**

- FastAPI task CRUD API (health, create, list, get, update, delete)
- 40 tests: 22 unit tests (tasks.py) + 18 integration tests (API)
- 85%+ coverage enforced in CI
- Pydantic v2 models with validation

**Docker:**

- Multi-stage build considerations, non-root user security
- HEALTHCHECK built into image
- docker-compose for local development

## 🚀 How to Run

```bash
cd Day-46-CICD
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests (same as CI)
pytest tests/ -v --cov=app

# Check style (same as CI)
ruff check app/ tests/

# Run API
uvicorn app.main:app --reload

# Docker
docker-compose up
```

**To activate the CI pipeline:**
Push this folder to GitHub → workflows run automatically on push.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
