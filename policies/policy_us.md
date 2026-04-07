# Content Violation Policy — United States (US)
## Platform Content Moderation Framework · Revision 2.4

---

## 1. Foundational Principles

This platform operates under a strong presumption in favor of free expression. Content should be allowed unless it presents a clear, direct, and serious harm. The burden of removal falls on the moderating party to demonstrate harm, not on the speaker to prove innocence. Controversial opinions, satire, political dissent, and uncomfortable truths are protected categories that must not be confused with violations.

Ambiguous content should default to allowance or flag rather than removal. Removal is reserved for cases where harm is unambiguous and significant.

---

## 2. Definitions

- **Targeted harassment**: Repeated, direct, threatening communication aimed at a specific individual with the intent to intimidate or cause fear.
- **Misinformation**: A false factual claim stated as established truth, where the falsehood is verifiable and the claim poses risk of real-world harm.
- **Hate speech**: Content that dehumanizes individuals on the basis of protected characteristics such as race, gender, religion, or nationality, using language that is degrading or calls for discrimination.
- **Safe content**: Opinion, satire, criticism, parody, disagreement, or expression that does not meet the threshold of the above categories.
- **Restricted content**: Borderline content that may be problematic in some contexts but does not clearly meet violation thresholds.

---

## 3. Violation Categories and Thresholds

### 3.1 Harassment and Threats
- **Actionable**: Explicit threats of physical violence directed at a named individual or identifiable group ("I will kill you", "I know where you live").
- **Not actionable**: Insults, heated arguments, competitive taunting, venting frustration, or hyperbolic statements not intended as literal threats.
- **Context matters**: A statement like "you should die" in a clearly sarcastic or gaming context is not a threat. In a personal dispute with prior threatening contact, it may be.

### 3.2 Misinformation
- **Actionable**: False health or safety claims stated as fact that could cause direct physical harm if acted upon (e.g., "drinking bleach cures disease", "this vaccine kills 1 in 10 people").
- **Not actionable**: Skepticism of institutions, questioning vaccine policies, political claims about effectiveness, disagreements with consensus, or speculation.
- **High threshold**: The claim must be factually false, stated as fact (not opinion), and directly harmful. Disputed scientific claims should be flagged at most, never removed unless they meet all three criteria.

### 3.3 Political Content
- Political speech, even extreme, is heavily protected. Content expressing support for political parties, candidates, or movements—including unpopular ones—must not be removed.
- Election-related false claims about voting procedures (e.g., "polling stations are closed") may be flagged with a correction label if verifiably false.
- Conspiracy theories about political figures are restricted but not removable unless they include direct incitement.

### 3.4 Hate Speech
- Content that calls for violence against a protected group is actionable.
- Slurs used in clearly educational or reporting contexts (quoting for documentation) are safe.
- General negative statements about a group without calls to action are restricted, not removable.

### 3.5 Safe Content
Any content that expresses opinion, disagrees with authority, criticizes public figures, uses satire, or engages in humor—even dark humor—is safe unless it meets the specific thresholds above.

---

## 4. Severity Levels

| Severity | Description |
|---|---|
| **Low** | Minor policy friction. Borderline language, unverified claims, mildly aggressive tone. No direct harm risk. |
| **Medium** | Clear policy concern but impact is limited. Content could mislead but is not viral. Threats are indirect or vague. |
| **High** | Explicit threats, false health claims with high reach, dehumanizing content. Direct harm risk. |
| **Critical** | Imminent physical threat, mass-scale misinformation during a crisis, content inciting coordinated violence. Immediate action required. |

---

## 5. Enforcement Actions

| Action | When to Apply |
|---|---|
| **Allow** | Default for all content unless a clear threshold is met. |
| **Flag** | Content that may be misleading or borderline. Adds a context label; content remains visible. Apply for medium severity misinformation, borderline hate speech, or unverified claims. |
| **Remove** | Explicit threats at high/critical severity, health misinformation that is demonstrably false and high-reach, content calling for violence against a group. |
| **Escalate** | Content involving public figures, potential legal issues, coordinated campaigns, or cases where context is genuinely ambiguous and a human reviewer should decide. |

---

## 6. Contextual Modifiers

- **Prior violations**: Two or more prior violations in the same category elevate severity by one level.
- **Engagement scale**: Content with >10,000 total interactions (likes + shares + comments) receives elevated scrutiny due to reach.
- **Satire indicators**: Explicit markers of satire or parody reduce severity classification.
- **User verification**: Verified accounts receive slight escalation (public responsibility), unverified accounts receive slight leniency.

---

## 7. Ambiguity Handling

When the intent or impact of content is genuinely unclear after reviewing all available context, default to the **less restrictive** action:
- If unsure between Allow and Flag → Flag
- If unsure between Flag and Remove → Flag
- If the content involves a public figure, legal nuance, or cross-jurisdictional context → Escalate

---

## Expected Output Mapping

```
violation_type: harassment | misinformation | hate_speech | restricted | safe
severity: low | medium | high | critical
action: allow | flag | remove | escalate
```
