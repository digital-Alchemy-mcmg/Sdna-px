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
