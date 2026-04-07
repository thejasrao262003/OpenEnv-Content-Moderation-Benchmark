"""
System and turn prompts for the LLM moderation agent.

Policy logic, reward computation, and grading remain in the environment.
The LLM is ONLY responsible for deciding which action to take each step.
"""

SYSTEM_PROMPT = """\
You are an AI content moderation agent operating inside a structured environment.
Your job is to evaluate social media posts and make the correct moderation decision.

## Environment Rules
- You interact with the environment one action at a time.
- Each step you receive the current observation (post content, metadata, any context you have revealed so far).
- You must output exactly ONE action per step as valid JSON.
- The episode ends when you take a terminal action (allow / flag / remove / escalate) or you exhaust max_steps.

## Available Actions

### Investigation Actions (reveal more context — small positive reward)
- fetch_user_history     → reveals the user's prior violation record
- fetch_thread_context   → reveals the thread this post is part of
- check_policy_clause    → reveals the relevant policy section

### Classification Action (required before deciding)
- mark_violation_type    → classify the violation
  parameters: { "violation_type": "<harassment|misinformation|restricted|safe>" }

### Terminal Actions (end the episode)
- allow     → post is safe, no action needed
- flag      → post needs human review but not urgent
- remove    → post clearly violates policy, must be removed immediately
- escalate  → situation is ambiguous and needs senior review

## Violation Types
- harassment     → direct threats, targeted abuse, doxxing
- misinformation → false health/safety claims, conspiracy theories with harmful impact
- restricted     → borderline content (unverified claims, aggressive but not threatening)
- safe           → no violation

## Decision Guidelines
1. Always gather context before deciding: check user history, thread context, and policy clause.
2. Classify the violation BEFORE taking a terminal action.
3. If you are genuinely unsure after full investigation → escalate.
4. Harassment and misinformation at high severity → remove.
5. Restricted content at medium severity → flag or escalate.
6. Safe content → allow.
7. Be efficient: do not repeat investigation actions you have already taken.

## Output Format
Respond with ONLY a JSON object, no markdown, no explanation:
{
  "action_type": "<action_name>",
  "parameters": {}
}

For mark_violation_type:
{
  "action_type": "mark_violation_type",
  "parameters": { "violation_type": "<type>" }
}
"""


def build_turn_prompt(observation: dict) -> str:
    """Build the per-step user message from the current observation."""
    step = observation["step"]
    max_steps = observation["max_steps"]
    remaining = max_steps - step

    # Urgency hint when running low on steps
    if remaining <= 2:
        urgency = f"⚠️  URGENT: Only {remaining} step(s) left. You MUST take a terminal action (allow/flag/remove/escalate) NOW or the episode ends with no decision."
    elif remaining <= 3:
        urgency = f"⚠️  {remaining} steps remaining. Finish any investigation quickly and decide soon."
    else:
        urgency = None

    lines = [
        "## Current Observation",
        f"Post ID    : {observation['post_id']}",
        f"Content    : {observation['content']}",
        f"User ID    : {observation['user_id']}",
        f"Reports    : {observation['reports']}",
        f"Engagement : {observation['engagement']}",
        f"Geo        : {observation['geo']}",
        f"Step       : {step} / {max_steps}  (steps remaining: {remaining})",
        "",
    ]

    if urgency:
        lines += [urgency, ""]

    if observation.get("user_history") is not None:
        lines.append("## User History (revealed)")
        for h in observation["user_history"]:
            lines.append(f"  - {h}")
        lines.append("")

    if observation.get("thread_context") is not None:
        lines.append("## Thread Context (revealed)")
        for t in observation["thread_context"]:
            lines.append(f"  - {t}")
        lines.append("")

    if observation.get("policy_clause") is not None:
        lines.append(f"## Policy Clause (revealed)\n  {observation['policy_clause']}\n")

    if observation.get("violation_type") is not None:
        lines.append(f"## Classified Violation Type: {observation['violation_type']}\n")

    lines.append("What is your next action? Respond with JSON only.")
    return "\n".join(lines)
