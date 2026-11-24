# Token Radar — transcript bundle status (LOCAL PREP, NOT SUBMITTED)

- Bounty: `token-radar-01`, $1,325, deadline **2026-12-14 10:00 UTC**
- Entrant: @finchbetter. Entry package complete (see PACKAGE.md).
- Local repo HEAD: `c28c0344fbfc25252b5d06a7922cd9bcc57e216b` (2026-11-23).
  HEAD moves if this file is updated; submit whatever HEAD is at submit time.
  No remote, no GitHub repo yet.

## 2026-11-23 thinking_reproduces fix (HEAD c28c034)

- Kit check on HEAD `2ef0084` failed only on `thinking_reproduces` (1.3% vs 30%
  required). Root cause, verified from the kit's own check code
  (`kitBaseOf`: the kit base skips `cli/` and `harness/`): the committed
  `kit/` tree — above all `kit/cli/makefun.mjs`, ~277k counted lines — counts
  in the denominator although no session could ever author it, and the
  generated `board.json` / `out/` files add ~19k more unwritable lines.
  Re-authoring outputs cannot reach 30% (needs ~96,750 authored lines);
  the fix is subtractive.
- This commit removes from the entry: the whole `kit/` tree, `kit.tar.gz`,
  `board.json`, `out/`, `competition.json`, `requirements.json`, `kit.json`,
  `bounty.html`, `counts.json`, `fit_part1.json`, `fit_results.json`.
  The entry is now 17 files: `main.ts`, `vendor/`, `dashboard/`,
  `screenshots/`, `LICENSE`, `MODEL.md`, `PACKAGE.md`, `TRANSCRIPTS.md`,
  `kit-inspection.md`, `fit_model.py`, `fit_part2.py`, `write_model_md.py`
  (the starter layout). The grader supplies `/input/snapshot.json`; `main.ts`
  takes `--input` for local runs.
- Local copies kept outside the repo: `~/workspace/makefun/kit-standalone/`
  (the kit, for running `check`/`bundle`) and
  `~/workspace/makefun/snapshot.json` (the sealed snapshot, sha256
  `42a71213519479f3a180cc5010cbbf6bd18a2447fa0ad29e4c5122b6c9184393`).
- `main.ts` re-run in the fix session (Node v24.22.1; no Node 22 binary in
  this sandbox) reproduced `out/` byte-identically before its removal:
  `out/board.json` `df586d84…`, `out/data.js` `aef7bcf0…`,
  `out/dossier.json` `330f5c39…`.
- Full numbers in `~/workspace/makefun/FIX.md` (outside the repo).

## What was verified 2026-11-21 ~23:00 UTC (dry-runs only, nothing uploaded)

Kit CLI `check` on the committed tree (`MAKEFUN_OFFLINE=1 node kit/cli/makefun.mjs check --repo . --worktree`):
- PASS: competition_open, snapshot/intake caps (56 files, 35,306,186 bytes),
  license_osi (MIT), entrypoint (main.ts at root, node22).
- FAIL (expected): transcripts_present — no bundle yet.
- Submission-time only: repo_public, repo_owner, repo_created_after_open,
  commit_in_repo, duplicate_snapshot — all need the public GitHub repo.

Kit CLI `bundle --dry-run` with the fixed flags (see below):
- **missing parts: []** — prompt, agent facts and MCP all resolved.
- 5 sessions, commit recorded, dirty false.
- Only remaining warning: **0 usage rows attached** (see §1).

## The working bundle command (dry-run verified)

Run from `~/workspace/makefun/token-radar/`:

```sh
MAKEFUN_OFFLINE=1 node kit/cli/makefun.mjs bundle --repo . \
  --out /tmp/token-radar-bundle.tar.gz --dry-run --json --no-discover \
  --prompt-file ~/workspace/makefun/token-radar-prompt.txt \
  --prompt-origin other \
  --prompt-via "typed by the user in the make.fun side chat at 2026-11-20 18:06 UTC, before this repo was created; the session cut drops the opener" \
  --provider meta --model muse-spark-1.3 --effort default --mcp none \
  --session ~/agents/agent-87eb9cb8-4db3-4a28-9cd3-1a6f6db778c3/sessions/87eb9cb8-4db3-4a28-9cd3-1a6f6db778c3.jsonl \
  --session ~/agents/agent-635f9e74-30f5-43f9-9ed4-4b03fa212b55/sessions/635f9e74-30f5-43f9-9ed4-4b03fa212b55.jsonl \
  --session ~/agents/agent-79558a0a-f001-4862-84d0-359c32444c97/sessions/79558a0a-f001-4862-84d0-359c32444c97.jsonl \
  --session ~/agents/agent-c765d065-3c7e-4417-9149-2e05c9bb328f/sessions/c765d065-3c7e-4417-9149-2e05c9bb328f.jsonl \
  --session ~/agents/agent-ec05be9b-dc30-4ec2-8ec2-4ab7e358424e/sessions/ec05be9b-dc30-4ec2-8ec2-4ab7e358424e.jsonl
```

Notes on the flags (all learned from failed dry-runs, not guessed):
- `--no-discover` + explicit `--session`: plain discovery finds 12 sessions,
  including 6–7 proactivity/research runs (Nov 20–21) that only read the entry
  and did not build it, plus the bundling run itself. The 5 above are the
  build sessions (Nov 20 18:30–19:19 UTC). Delivery should re-verify with
  `check --transcripts <bundle>` that no builder session is missing.
- Prompt: the true opener is the user's side-chat message
  2026-11-20 18:06 UTC (saved verbatim in
  `~/workspace/makefun/token-radar-prompt.txt`). Plain discovery picks
  "今次唔要" (a later Anthropic-IPO message in the same long-lived session).
  `--prompt-origin typed` alone is refused because the session cut drops the
  opener (bundle cuts each session to records after the repo was first named;
  the opener predates the repo). `other` + the `--prompt-via` explanation
  above is the combination that clears the gate in dry-run.
- `--provider meta --model muse-spark-1.3 --effort default`: clears the
  agent-facts missing items. `--mcp none`: the build used file/exec/browser
  tools only; the sessions show no MCP server use (the 8 "mcp" hits in the
  top session are tool-output text, not MCP calls).
- Prompt file and dry-run JSON are kept OUTSIDE the repo:
  `~/workspace/makefun/token-radar-prompt.txt`,
  `~/workspace/makefun/token-radar-bundle-dryrun-2026-11-21.json`,
  `~/workspace/makefun/token-radar-check-2026-11-21.json`.

## §1 Remaining blocker: usage rows (needs the app-side muse.db tool)

`muse.db` is NOT present anywhere in this sandbox (searched whole home),
so the rows cannot be fetched here. In a main-agent turn with the muse.db
tool, run this SELECT with the 5 build agent_ids (agent_id == session_id
for muse-app sessions), write the rows unchanged (one JSON object per line)
to a file, then re-run the bundle command above with
`--muse-usage <file>` (drop `--dry-run` for the real bundle):

```sql
SELECT u.agent_id AS agent_id, u.message_id AS message_id, u.created_at AS created_at, u.input_tokens AS input_tokens, u.output_tokens AS output_tokens, a.model AS model FROM agent.agent_message_token_usage u JOIN agent.agents a ON a.agent_id = u.agent_id WHERE u.agent_id IN ('87eb9cb8-4db3-4a28-9cd3-1a6f6db778c3','635f9e74-30f5-43f9-9ed4-4b03fa212b55','79558a0a-f001-4862-84d0-359c32444c97','c765d065-3c7e-4417-9149-2e05c9bb328f','ec05be9b-dc30-4ec2-8ec2-4ab7e358424e') ORDER BY u.created_at DESC LIMIT 500
```

Then run `check --repo . --transcripts <bundle.tar.gz>` (HEAD, not worktree)
and confirm the transcript gate passes before submitting.

## Still missing for submission (unchanged)

1. **GitHub account name** (asked 2026-11-20 ×3 and 2026-11-21 11:20 PST,
   no reply): create the public repo, push commit `9071682a…` (or later HEAD).
2. Usage rows (§1) + real bundle + kit `check` on bundle.
3. Submit before 2026-12-14 10:00 UTC (≤5/day, ≤10 total; last receipt final).
