# Agent Bricks CLI Demo — Meridian Labs

Companion files for the Agent Bricks CLI tutorial.
Follow along to build and deploy a Databricks agent that answers customer health questions using a custom `get_region_health` tool.

**Verified:** `databricks-agentbricks` 0.4.0 · Python 3.11+ · 2026-10-07

---

## Files in this repo

| File | Purpose |
|------|---------|
| `region_health.py` | Custom LangGraph tool — copy into `<project>/agent/tools/` |
| `meridian_region_health_q3_2026.csv` | Same Q3 2026 data as a CSV (36 rows) for reference |

---

## Setup checklist

### Workspace
- [ ] Trial or paid Databricks workspace (Free Edition not officially supported — see [Free Edition](#free-edition))
- [ ] `uv tool install databricks-agentbricks` → `agentbricks --version` shows 0.4.0+
- [ ] Compute > Apps opens without error
- [ ] The model `system.ai.claude-sonnet-4-5` is available in your workspace

### Local machine
- [ ] Python 3.11+
- [ ] `uv` installed: `uv --version`
- [ ] Databricks CLI installed: `databricks --version`
- [ ] `uuidgen` available (macOS ships it)

---

## How to run commands with uv

**Before the project exists** (install, login, init) — run plain:
```
agentbricks ...
```

**Inside the project folder** (where `agent.toml` lives) — prefix every command:
```
uv run agentbricks ...
```

---

## Step 1 — Install & login

```bash
uv tool install databricks-agentbricks
agentbricks --version
```

```bash
databricks auth login --host https://<your-workspace-url> --profile meridian
agentbricks login --profile meridian
```

---

## Step 2 — Scaffold

```bash
agentbricks init --framework langgraph meridian-agent
cd meridian-agent
cp .env.example .env
```

Edit `.env`:
```
DATABRICKS_CONFIG_PROFILE=meridian
```

> `init` prints store names with a random 6-letter token, e.g. `meridian-agent-xxxxxx-memory`. That is expected.

---

## Step 3 — Add the tool

```bash
cp /path/to/region_health.py agent/tools/
```

> The file goes into `agent/tools/` — **not** the project root.
> Do not copy the entire demo folder into your project; deploy uploads everything in the folder.

Verify the agent discovers it:
```bash
uv run python -c "from agent.tools import all_tools; print([t.name for t in all_tools()])"
```

Expected:
```
['get_region_health', 'get_current_time', 'send_message']
```

---

## Step 4 — Run locally

```bash
uv run agentbricks dev
```

Open http://localhost:8000

**Prompt 1 — discovery:**
```
Compare customer health across all our regions for Q3. Anything unusual?
```

Expected numbers:
```
NA      churn 2.73%  first response 3.1h  CSAT 4.48
Europe  churn 3.10%  first response 3.5h  CSAT 4.37
APAC    churn 8.47%  first response 8.7h  CSAT 3.60   ← anomaly
LATAM   churn 3.68%  first response 3.8h  CSAT 4.29
Company churn 4.21%
```

**Prompt 2 — drill down:**
```
Break APAC down by tier. Where is the problem worst?
```

Expected:
```
Free 9.55% churn / 11.5h  |  Pro 6.07% / 9.0h  |  Enterprise 2.84% / 5.6h
```

**Prompt 3 — human approval:**
```
Send a message to the APAC support lead with a short summary of this problem.
```

An approval card appears — `send_message` is in `REQUIRE_APPROVAL`. Click Approve. The template tool is a stub; nothing is actually sent.

Open the Traces URL printed in the terminal to inspect model and tool spans.

Stop the server: `Ctrl+C`

---

## Step 5 — Bind stores & deploy

```bash
uv run agentbricks sessions bind meridian-agent-sessions
uv run agentbricks memory bind meridian-agent-memory
uv run agentbricks tools list
```

After binding, `agent.toml` updates with the new store names.

```bash
uv run agentbricks deploy meridian-agent
```

Expected app name: `agent-bricks-meridian-agent`. Check it in Compute > Apps.

---

## Step 6 — Use the deployed app

Open the URL from the deploy output, or:
```bash
uv run agentbricks deployments get agent-bricks-meridian-agent
```

**Test memory — chat 1:**
```
Remember this: I own the APAC region, so always show me APAC numbers first.
```

Click "New session", then **chat 2:**
```
Give me a quick customer health update.
```

Expected: agent calls recall and puts APAC first. Open the Memory pane in the sidebar to see the stored entry.

**Inspect stores:**
```bash
uv run agentbricks sessions list --store meridian-agent-sessions
```

```bash
uv run agentbricks -o json memory entries list --store meridian-agent-memory --actor-id <your-workspace-email>
```

> `-o json` must come **before** `memory`. Without it the text view hides entry content.

**Invoke via API:**
```bash
uv run agentbricks endpoint invoke agent-bricks-meridian-agent \
  --path /api/invocations \
  --routing-key demo-1 \
  --json "{\"id\":\"$(uuidgen)\",\"session_id\":\"demo-1\",\"input\":[{\"role\":\"user\",\"content\":\"Which region has the highest churn?\"}]}"
```

**Observability:**
```bash
uv run agentbricks deployments list
uv run agentbricks deployments logs agent-bricks-meridian-agent
uv run agentbricks tracing list
```

Workspace: Experiments > `/Shared/agentbricks_traces/<project-name-with-token>`

---

## Shut down

**Stop** — keeps app, URL, code and stores; no compute cost:
```bash
uv run agentbricks deployments stop agent-bricks-meridian-agent
```

**Delete app and its Runtime Store:**
```bash
uv run agentbricks deployments delete agent-bricks-meridian-agent
```

**Delete memory and session stores** — separate resources, billed separately:
```bash
uv run agentbricks memory stores delete meridian-agent-memory
uv run agentbricks sessions stores delete meridian-agent-sessions
```

Verify:
```bash
uv run agentbricks deployments list
```

> Delete with the CLI, not the workspace UI — the UI skips Runtime Store cleanup.
> Every delete command asks "are you sure". Type `y` or add `-y` to skip.

---

## Backup prompts

Use these if the agent doesn't do what's expected:

1. **Agent ignores the tool:** `Use the get_region_health tool with region "all" and tell me which region stands out.`
2. **Tier breakdown is vague:** `Call get_region_health for APAC and show the tiers in a table.`
3. **Approval card doesn't appear:** `Use the send_message tool to message apac-lead@meridianlabs.example with: "APAC churn is 8.5% in Q3, please review."`
4. **Memory not used:** `Please use your remember tool to save that I own the APAC region.` → (new chat) `What do you remember about me? Use your recall tool.`
5. **Quick sanity check:** `What time is it right now? Use your tool.`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Databricks auth is not configured` on dev start | `DATABRICKS_CONFIG_PROFILE` in `.env` doesn't match a profile in `~/.databrickscfg` |
| uv Python version error | `uv python install 3.12`, then re-run |
| `agentbricks: command not found` | `uv tool update-shell`, open a new terminal; or use `uv run agentbricks` inside the project |
| Model call fails / model not found | `MODEL` in `agent/agent.py` isn't available in your workspace — pick another `system.ai` model in the chat app picker |
| Agent never calls `get_region_health` | `region_health.py` is not in `agent/tools/`. Run the check command from Step 3, restart dev, click New session |
| Memory doesn't work in dev | Expected — memory is only active after deploy |
| Chat history lost after restarting dev | Expected — local sessions are in-process only |
| `session_id must be provided as a top-level invocation field` | You're using the old 0.3.x request format. Use the command in Step 6 (already updated) |
| `No such option: --session-id` | You're on 0.4.0 — use `--routing-key` as shown in Step 6 |
| Deploy fails on scopes | Only for tools with `auth = "user"`. Re-run with `--allow-user-scope-update` |

---

## Free Edition

Free Edition is **not officially supported**. Use a trial or paid workspace.

- Managed memory and sessions (Beta) run on Lakebase. Free Edition allows **one** Lakebase project per account.
- Default deploy creates a per-app Lakebase project for the Runtime Store — this can hit the one-project limit if you already have one.
- Free Edition apps: max 3 per account, stop after 24 hours.
- **Possible light path (untested):** `agentbricks init --server custom` creates a plain FastAPI agent with no Runtime Store, memory, or session stores. Local `uv run agentbricks dev` may work if the model call succeeds.
