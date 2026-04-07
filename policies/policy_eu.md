# Content Violation Policy — European Union (EU)
## Platform Content Moderation Framework · Revision 3.1

---

## 1. Foundational Principles

This platform operates under a framework of proactive harm prevention. Under EU Digital Services Act obligations, the platform has a duty of care to prevent its services from being used to spread content that undermines public safety, democratic institutions, or the fundamental rights of individuals. Expression is protected, but not at the cost of measurable societal harm.

When content may cause harm, the default action should be preventative. The burden shifts toward the platform to ensure safety. Ambiguity should trigger escalation or temporary flagging rather than unchecked distribution.

---

## 2. Definitions

- **Targeted harassment**: Any content that intimidates, threatens, or degrades a specific individual, including sustained campaigns, unwanted sexual content, doxxing attempts, and identity-based attacks.
- **Misinformation**: False information presented as fact, particularly in domains of health, safety, elections, and public institutions. Includes content that contradicts established scientific or regulatory consensus where the misrepresentation poses public harm risk.
- **Hate speech**: Content that incites discrimination, hostility, or violence against persons based on protected characteristics including race, ethnicity, religion, gender, sexual orientation, or disability.
- **Safe content**: Criticism, satire, journalism, research, political commentary, and expression that is clearly non-harmful or serves a legitimate public interest.
- **Restricted content**: Content that is borderline, context-dependent, or potentially violating but not clearly actionable without additional review.

---

## 3. Violation Categories and Thresholds

### 3.1 Harassment and Threats
- **Actionable at high severity**: Any direct threat of physical harm to a named person, whether explicit ("I will harm you") or implied through intimidating personal details.
- **Actionable at medium severity**: Sustained targeted abuse of a private individual, sharing of private information without consent, sexualized harassment.
- **Context**: Public figures accept higher levels of criticism, but threats to their physical safety are still actionable.

### 3.2 Misinformation — Elevated Priority Category
This is a priority category under EU regulations. The threshold for action is lower than in other regions.
- **Remove at high severity**: Health misinformation contradicting medical consensus and carrying significant public harm potential (anti-vaccine falsehoods presented as fact, medical treatment hoaxes). This applies even if engagement is moderate, given virality risk.
- **Flag at medium severity**: Unverified claims about public health, election processes, or safety of products that are circulating widely. Add context labels and restrict amplification.
- **Escalate**: Coordinated inauthentic behavior, state-sponsored disinformation campaigns, or content originating from known unreliable sources.
- **Allow**: Genuine scientific debate, policy disagreements, qualified uncertainty statements by credentialed individuals.

### 3.3 Political Content
- Political speech is protected but subject to truthfulness standards in electoral contexts.
- False claims about voting procedures, electoral candidates, or outcomes must be flagged with corrections if verifiably false.
- Extremist political content that incites hatred or calls for violence must be removed.
- Opinion and criticism of governments, institutions, and public officials is fully protected.

### 3.4 Hate Speech — Elevated Priority Category
- The EU applies a stricter standard to hate speech than most other regions.
- Content that dehumanizes or calls for discrimination against any group based on protected characteristics is actionable at medium severity or above.
- At high severity (incitement to violence against a group): remove.
- At medium severity (dehumanization, slurs used offensively): flag and restrict reach.

### 3.5 Safe Content
Journalistic content, satire (clearly marked), academic discussion, historical documentation, and political commentary are safe unless they cross into the categories above.

---

## 4. Severity Levels

| Severity | Description |
|---|---|
| **Low** | Minor violation potential. Borderline language, isolated false claim with negligible reach, vague negativity. |
| **Medium** | Clear policy friction. False health claim with moderate reach, targeted abuse, offensive but non-inciting hate speech. Requires action but not urgency. |
| **High** | Significant harm potential. Direct threat, high-reach misinformation contradicting safety guidance, incitement to discrimination. Requires prompt removal or flagging. |
| **Critical** | Imminent harm. Active threat, crisis misinformation spreading rapidly, coordinated disinformation during elections or public health emergencies. Immediate removal. |

---

## 5. Enforcement Actions

| Action | When to Apply |
|---|---|
| **Allow** | Content that meets no violation threshold, including all protected expression categories. |
| **Flag** | Medium severity violations, borderline content, unverified claims with moderate reach. Content remains visible but with a context label and reduced amplification. |
| **Remove** | High or critical severity violations. Explicit threats, high-reach health misinformation contradicting consensus, incitement to group violence. |
| **Escalate** | Cases involving potential legal violations, coordinated campaigns, ambiguous political content, or content crossing multiple categories simultaneously. |

---

## 6. Contextual Modifiers

- **Prior violations**: One or more prior violations elevates severity by one level.
- **Engagement scale**: Content with >5,000 total interactions (lower threshold than US) receives elevated scrutiny. Content with >20,000 interactions in misinformation or hate speech categories defaults to high severity.
- **Source credibility**: Content from accounts previously linked to inauthentic behavior elevates severity.
- **Crisis context**: During declared public health emergencies or election periods, misinformation thresholds are lowered by one level (medium becomes high, low becomes medium).
- **Geo targeting**: Content specifically targeting EU residents from external sources is subject to full policy application.

---

## 7. Ambiguity Handling

When content is genuinely ambiguous, the EU framework defaults to the **more protective** action:
- If unsure between Allow and Flag → Flag
- If unsure between Flag and Remove → Flag with escalation for human review
- Content involving electoral integrity, public health, or fundamental rights → always Escalate if uncertain
- Never allow clearly borderline high-reach content without escalation

---

## Expected Output Mapping

```
violation_type: harassment | misinformation | hate_speech | restricted | safe
severity: low | medium | high | critical
action: allow | flag | remove | escalate
```
