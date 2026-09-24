# SDNA-PX Shared Agent Check-In Cadence

## Authority
User directive: every active agent collaborating through this repository must install a recurring check-in at **least twice per hour**.

## Required cadence
- Target cadence: **every 30 minutes or faster**.
- Each agent must use the fastest recurring schedule its own scheduler reliably supports, provided it is no slower than every 30 minutes.
- Each agent must report back into the repository:
  - scheduler/platform name;
  - installed cadence;
  - next scheduled check-in;
  - last successful check-in;
  - any scheduler limitation preventing compliance.

## Agents
- Spark
- Meta
- GPT

## Shared control-surface behavior
On each check-in:
1. Read current `main` state and recent commits.
2. Read this control file and any active task/repair contracts.
3. Detect new work, conflicts, failed CI, or unresolved handoffs.
4. Act within granted authority.
5. Write durable results, receipts, or blockers back to the repository.
6. Do not rely on the user to carry messages between agents.

## Limitation disclosure
If an agent's scheduler cannot run at least every 30 minutes, it must explicitly record that limitation here or in a sibling receipt. It must not claim compliance at a slower cadence.

## GPT scheduler limitation
ChatGPT's native scheduled-task system currently supports a maximum frequency of **once per hour**. GPT therefore cannot satisfy the twice-per-hour requirement with its native scheduler. GPT must not pretend otherwise. Until a faster supported runner is available, GPT should rely on repository-triggered/manual invocation for additional checks and record this limitation transparently.


## Required staggered-runner fallback

If an agent or platform limits any single scheduled task to once per hour, that limitation does **not** satisfy the twice-per-hour requirement by itself and is **not** an acceptable reason to fall back to hourly checking.

Use multiple independent hourly runners against the same target.

Canonical fallback pattern:

- Runner A: hourly at `:15`
- Runner B: hourly at `:45`

Combined effective cadence: one repository check every 30 minutes.

Equivalent staggered pairs are acceptable if they preserve a maximum 30-minute gap.

Example:
- `:00` + `:30`
- `:15` + `:45`

Requirements:
1. Both runners must target the same Sdna-px control surface.
2. Both must read current `main`, recent commits, CI, active contracts, and unresolved handoffs.
3. Both must write durable results/receipts back to the repository when action is required.
4. The agent must record both installed schedules and next-run times.
5. Do not claim a single hourly runner is the platform maximum if multiple independent runners can be staggered.
6. If the platform limits the *account as a whole* to fewer than two executions per hour, record the exact platform constraint and evidence. Otherwise, install the staggered pair.

## Current GPT implementation
GPT uses two independent hourly runners:
- hourly at `:15`
- hourly at `:45`

Spark and Meta should implement the same pattern whenever their scheduler has a per-task hourly cap.
