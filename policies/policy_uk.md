# Content Violation Policy — United Kingdom (UK)
## Platform Content Moderation Framework · Revision 2.2

---

## 1. Foundational Principles

The United Kingdom framework is built on the principle of proportionate harm prevention. The platform has a legal and ethical duty to protect users from content that causes demonstrable harm, while preserving the right to free expression in matters of public interest, satire, political commentary, and legitimate debate. The Online Safety Act framework places responsibility on platforms to proactively identify and mitigate harmful content.

This policy takes a balanced approach: more protective than the US model but with greater tolerance for robust political and social debate than some continental European frameworks. The emphasis is on protecting individuals—especially vulnerable populations—while enabling healthy public discourse.

---

## 2. Definitions

- **Targeted harassment**: Repeated, unwanted communication that causes alarm, distress, or fear to a specific person. Includes pile-ons, coordinated targeting, unwanted sexual contact, and identity-based abuse.
- **Misinformation**: False statements of fact presented as true, particularly in health, safety, and electoral domains. Distinguished from opinion and from disputed evidence where scientific consensus is genuinely unsettled.
- **Hate speech**: Content that stirs up hatred against a group based on protected characteristics, including race, religion, sex, sexual orientation, disability, or gender identity. Includes content that dehumanises or calls for discrimination.
- **Safe content**: Criticism, satire, journalism, political commentary, academic discussion, religious debate, and expression that serves a legitimate purpose.
- **Restricted content**: Borderline material requiring contextual assessment before action.

---

## 3. Violation Categories and Thresholds

### 3.1 Harassment and Threats
- **Remove at high/critical severity**: Explicit threats of physical violence, sexual violence, or threats against a person's family. Sharing of private personal information with intent to harm. Sustained coordinated harassment campaigns.
- **Flag at medium severity**: Persistent unwanted contact, targeted identity-based insults, content directed at a specific individual designed to cause distress.
- **Allow**: Heated disagreement, robust criticism, satire of public figures (even uncomfortable), general expressions of frustration not targeted at an individual.

### 3.2 Misinformation
- **Remove at high severity**: Health misinformation directly contradicting established medical guidance where acting on the false claim could cause physical harm. This includes false claims about vaccine safety stated as fact, false treatment claims, and misinformation about contagious diseases.
- **Flag at medium severity**: Unverified health claims with significant reach. Electoral misinformation about voting procedures. False claims about public safety incidents.
- **Allow**: Policy debates about health interventions, criticism of regulatory bodies, scientific scepticism that does not assert false facts, political disagreements about health strategy.
- **Election period uplift**: During election periods, electoral misinformation thresholds are lowered and faster escalation is expected.

### 3.3 Political Content
- Political speech is broadly protected, including criticism of the government, political parties, elected officials, and institutions.
- False claims about specific voting procedures or electoral results that could suppress votes may be flagged with corrections.
- Extremist content that incites violence or overthrow of democratic institutions is actionable.
- Content that endorses illegal discrimination against groups based on protected characteristics is actionable.

### 3.4 Hate Speech
- The UK applies a moderate-to-strict standard consistent with its legal framework.
- Content that stirs up hatred against religious groups, racial groups, or LGBTQ+ individuals is actionable from medium severity upward.
- At medium severity (dehumanising language, offensive stereotypes, non-inciting slurs): flag and restrict reach.
- At high severity (explicit incitement to hatred, calls for discrimination, dehumanising rhetoric used to target a community): remove.
- Criticism of religion, including robust or offensive criticism, is protected. Incitement against religious communities is not.

### 3.5 Online Safety for Minors
- Content that targets minors for any form of harm is critical severity and must be removed immediately with escalation.
- Content that normalises self-harm, suicide, or eating disorders where it could influence vulnerable individuals should be flagged and reach-restricted.

### 3.6 Safe Content
Political satire (a protected tradition in UK culture), press freedom, academic research, journalism, fiction, and public interest content are safe unless they clearly meet violation thresholds.

---

## 4. Severity Levels

| Severity | Description |
|---|---|
| **Low** | Minor borderline content. Mild offensive language, unverified isolated claim, vague negativity. Low reach. |
| **Medium** | Clear policy friction. Targeted insult, moderately false health claim with growing reach, offensive hate speech. Requires action but not immediate removal. |
| **High** | Significant harm. Explicit threat, high-reach health misinformation, clear incitement of hatred. Prompt removal or flagging required. |
| **Critical** | Immediate risk. Active threat with personal information, content endangering a minor, mass-scale misinformation during a crisis or election. Immediate removal and escalation. |

---

## 5. Enforcement Actions

| Action | When to Apply |
|---|---|
| **Allow** | Default for political content, robust debate, satire, religious commentary, and anything that does not meet a clear violation threshold. |
| **Flag** | Medium severity violations, borderline content, unverified health claims with reach. Content visible but with label and reduced amplification. |
| **Remove** | High or critical severity violations: explicit threats, high-reach health misinformation, incitement to hatred, harm to minors. |
| **Escalate** | Legally sensitive content, electoral integrity concerns, coordinated behaviour, ambiguous religious or political content, safeguarding concerns involving minors. |

---

## 6. Contextual Modifiers

- **Prior violations**: One or more prior violations elevates severity by one level.
- **Engagement scale**: >5,000 total interactions triggers elevated scrutiny. >15,000 for misinformation or hate speech categories defaults to high severity.
- **Vulnerability context**: Content targeting individuals who are known to be minors, or communities known to be at heightened risk, elevates severity.
- **Public interest test**: Content that would otherwise be flagged may be allowed if it passes a clear public interest test (journalism, research, whistleblowing).
- **Election period**: During a general election period (from dissolution to result), electoral misinformation severity is elevated by one level.
- **Satire marker**: Explicit satirical framing reduces severity by one level for speech categories.

---

## 7. Ambiguity Handling

The UK framework applies a context-sensitive approach to ambiguity:
- Political content, even extreme → Allow unless explicit incitement is present
- Health content that is unverified but not demonstrably false → Flag
- Content targeting a specific individual → Err toward Flag or Remove if distress is likely
- Content crossing categories (e.g., political + communal) → Escalate
- Any content potentially involving minors → Escalate immediately, do not allow or delay

---

## Expected Output Mapping

```
violation_type: harassment | misinformation | hate_speech | restricted | safe
severity: low | medium | high | critical
action: allow | flag | remove | escalate
```
