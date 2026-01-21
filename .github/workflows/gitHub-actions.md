
## Overview

This workflow spins up **crAPI** using **Docker Compose** on a GitHub-hosted Linux runner, waits until the app is reachable, runs **Robot Framework API security tests** against it, uploads the **Robot reports** as artifacts, then **tears everything down** (even if tests fail).

---

## Header + Triggers

### `name: API Security Robot Tests with GitHub Action`

This is just the workflow display name you see in the Actions tab.

### `on:`

This defines when the workflow runs.

* `workflow_dispatch:`
  ✅ Allows you to run it manually from GitHub UI (Actions → Run workflow).

* `push: branches: ["main"]`
  ✅ Runs on every push to `main` (e.g., merging PRs, direct commits).

* `pull_request:`
  ✅ Runs on PRs targeting your repo (default PR events: opened, synchronize, reopened).
  This is important because it gives you test feedback *before* merging.

---

## Job Definition

### `jobs: robot-tests:`

You have one job called **robot-tests**.

### `runs-on: ubuntu-latest`

The job runs on a fresh GitHub-hosted VM (Linux).
It comes with `docker` preinstalled, and usually `docker compose` is available too.

---

## Steps (executed in order)

### 1) Checkout repository

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```

This pulls your repo’s code into the runner’s filesystem so later steps can access:

* `deploy/docker/docker-compose.yml`
* `tests/` Robot files
* any configs/scripts

Without checkout, there’s nothing to run.

---

### 2) Start crAPI (Docker Compose)

```yaml
- name: Start crAPI
  working-directory: deploy/docker
  run: |
    docker compose pull
    docker compose -f docker-compose.yml --compatibility up -d
    docker compose ps
```

**What’s happening:**

* `working-directory: deploy/docker`
  Ensures compose runs where your `docker-compose.yml` is located.

* `docker compose pull`
  Downloads the required images from registries (faster than building).

* `docker compose ... up -d`
  Starts all services defined in the compose file (web, identity, dbs, etc.) in **detached mode**.

* `--compatibility`
  Tells Compose to honor some legacy/swarm-style resource constraints (like CPU/memory limits) if present.
  Not always necessary, but can prevent warnings or behavior differences depending on the compose file.

* `docker compose ps`
  Shows which containers are running (good for debugging logs).

**Why this matters:** crAPI is multiple services, so Compose is the right tool.

---

### 3) Wait for crAPI to be ready (health check loop)

```yaml
- name: Wait for crAPI to be ready
  run: |
    for i in {1..60}; do
      if curl -sSf http://localhost:8888 >/dev/null; then
        echo "crAPI is up"
        exit 0
      fi
      echo "Waiting for crAPI..."
      sleep 5
    done
    echo "crAPI did not start in time"
    exit 1
```

This prevents tests from starting too early.

**Details:**

* Loop runs up to **60 times**
* Sleeps **5 seconds** between tries
  → maximum wait time = 60 × 5 = **300 seconds (5 minutes)**

**curl flags:**

* `-s` silent (less noise)
* `-S` still shows errors if they happen
* `-f` fail on HTTP error codes (like 404/500)

✅ If HTTP responds successfully, workflow continues.
❌ If not ready within 5 minutes, workflow fails early with a clear message.

---

### 4) Set up Python 3.11

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.11"
```

Robot Framework runs on Python. This installs/activates Python 3.11 on the runner.

---

### 5) Install Robot Framework + RequestsLibrary

```yaml
- name: Install Robot Framework
  run: |
    python -m pip install --upgrade pip
    pip install robotframework robotframework-requests
```

Installs:

* `robotframework` → the test runner
* `robotframework-requests` → lets Robot send HTTP requests (API testing)

Note: If your tests also use other libraries (JSON, faker, selenium, etc.) you’d add them here or use a `requirements.txt`.

---

### 6) Run Robot tests

```yaml
- name: Run Robot tests
  env:
    BASE_URL: "http://localhost:8888"
  run: |
    mkdir -p reports
    robot -d reports tests
```

**What this does:**

* Exports environment variable `BASE_URL` for the test runtime
  Your Robot tests can read it like:

  * `${ENV:BASE_URL}` (Robot built-in environment access)
  * or via a variable file / library setup

* `mkdir -p reports`
  Creates an output folder.

* `robot -d reports tests`
  Runs all robot tests under `tests/` and writes outputs to `reports/`.

Robot typically generates:

* `report.html`
* `log.html`
* `output.xml`

Those are exactly what you want to keep as artifacts.

---

### 7) Upload Robot reports (always)

```yaml
- name: Upload Robot reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: robot-reports
    path: reports/
```

`if: always()` is important:

* Even if tests fail, you still get logs + HTML report to debug.

Artifacts appear in the workflow run summary → downloadable as a zip.

---

### 8) Stop crAPI (always)

```yaml
- name: Stop crAPI
  if: always()
  working-directory: deploy/docker
  run: |
    docker compose -f docker-compose.yml down -v
```

This cleans up the environment.

* `down` stops and removes containers + network
* `-v` also removes volumes (database data, etc.)
  ✅ ensures every run starts clean
  ✅ avoids “dirty state” between runs

`if: always()` means cleanup happens even if something earlier fails.

---

## What Next!

### Common improvements (very practical)

- Cache pip dependencies (faster runs)
- Save docker logs on failure (super helpful)
- Use a healthcheck from compose instead of only curl
- Use requirements.txt for consistent versions
- Pin Robot libs versions to avoid surprise upgrades


