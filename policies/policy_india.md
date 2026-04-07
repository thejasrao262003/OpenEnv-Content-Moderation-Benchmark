# Content Violation Policy — India (IN)
## Platform Content Moderation Framework · Revision 2.7

---

## 1. Foundational Principles

India presents a uniquely complex moderation environment defined by extraordinary linguistic diversity, deep religious and caste sensitivities, a rapidly growing internet population, and a history of communal tensions that can be triggered and amplified by online content. This policy recognizes that content which may be benign in other regions can carry severe real-world consequences in the Indian context.

At the same time, political discourse and religious expression are deeply embedded in Indian public life. This policy does not seek to suppress political speech or theological debate, but to prevent content that weaponizes identity, inflames communal divisions, or spreads dangerous falsehoods within a high-reach social media environment.

---

## 2. Definitions

- **Communal content**: Content that pits religious, caste, ethnic, or regional groups against each other using inflammatory, dehumanizing, or threatening language.
- **Targeted harassment**: Direct threats, sustained abuse, or doxxing aimed at a specific individual or community.
- **Misinformation**: False factual claims presented as truth, especially in domains of health, religion, and communal events where false claims have historically preceded physical violence.
- **Political content**: Expression of political opinions, criticism of government or public officials, coverage of elections or civic matters.
- **Safe content**: Opinion, satire, religious discussion without incitement, political commentary, journalism, and civic debate.
- **Restricted content**: Content touching sensitive categories that requires context before a determination can be made.

---

## 3. Violation Categories and Thresholds

### 3.1 Communal and Religious Content — Priority Category
This is the highest-priority category in the Indian context given the documented history of online content contributing to communal violence.
- **Remove at high/critical severity**: Content that directly calls for violence against a religious community, caste group, or ethnic minority. Content that spreads verifiably false claims about atrocities committed by a religious group. Content that uses imagery, slogans, or rhetoric associated with documented incitement of communal violence.
- **Flag at medium severity**: Content that uses derogatory language about a religious or caste group without direct incitement. Content that promotes stereotypes likely to inflame tensions.
- **Allow**: Theological debate, criticism of religious practices or institutions, interfaith dialogue, academic discussion of religion, political commentary involving religion.

### 3.2 Harassment and Threats
- **Actionable at high severity**: Explicit death threats, threats of sexual violence, doxxing of private individuals, sustained targeted campaigns.
- **Actionable at medium severity**: Identity-based abuse targeting gender, caste, religion, or regional identity of an individual.
- **Context**: Aggressive political criticism of public figures is generally allowed. Threats to their physical safety are not.

### 3.3 Misinformation — High Sensitivity in Health and Communal Domains
- **Remove at high severity**: Health misinformation that has already been acted upon or is likely to be acted upon imminently (e.g., false claims that a specific food or medicine kills or protects during an outbreak). Communal misinformation alleging attacks or crimes by a specific group that are verifiably false.
- **Flag at medium severity**: Unverified viral health claims. Unverified reports of communal incidents.
- **Allow**: Political misinformation about parties or politicians (falls under political speech). General scepticism or questioning of government health guidance.

### 3.4 Political Content — Protected Category
Political speech in India is broadly protected and moderation should be minimal.
- Content supporting or opposing any political party, leader, or policy is allowed regardless of controversy.
- False claims about voting procedures or election results may be flagged with corrections if verifiably false.
- Calls for peaceful protest, even confrontational language toward political adversaries, are protected.
- Content inciting violence against political opponents is actionable.

### 3.5 Safe Content
General political criticism, religious commentary, regional jokes without dehumanization, opinions on social issues, satire (clearly indicated), and civic debate are all safe.

---

## 4. Severity Levels

| Severity | Description |
|---|---|
| **Low** | Borderline language, single unverified claim with low reach, mild identity-based insult. |
| **Medium** | Offensive communal or caste language without direct incitement, unverified viral claim with moderate reach, personal abuse without threat. |
| **High** | Direct incitement of communal violence, explicit threats, high-reach health misinformation, false reports of communal attacks. |
| **Critical** | Immediate incitement during an active communal incident, death threats with personal information, viral false claims actively inflaming an ongoing situation. |

---

## 5. Enforcement Actions

| Action | When to Apply |
|---|---|
| **Allow** | Political content (broadly), religious debate and criticism, general social commentary, personal opinions. |
| **Flag** | Communal content at medium severity, unverified viral health claims, borderline incitement. Add context and reduce amplification. |
| **Remove** | Communal incitement at high/critical severity, explicit threats, health misinformation with active harm risk. |
| **Escalate** | Content involving ongoing real-world incidents, content from accounts with prior communal violations, ambiguous content involving high-profile figures or disputes. |

---

## 6. Contextual Modifiers

- **Prior violations**: Prior communal or incitement violations elevate severity by one level.
- **Engagement scale**: Content with >5,000 interactions involving communal or misinformation categories defaults to high severity. Content with >15,000 interactions defaults to critical if it touches communal triggers.
- **Active situation context**: During a documented ongoing communal incident, all related content's severity is elevated by one level.
- **Political content downgrade**: Content classified as political (even if it uses strong language) should have severity downgraded by one level unless it directly incites violence.
- **Language context**: Content in regional languages (Hindi, Tamil, Bengali, etc.) may carry cultural context not visible in translation; flag for regional language review when in doubt.

---

## 7. Ambiguity Handling

Given the potential for real-world harm from communal content, ambiguity should default toward caution in the following domains:
- Communal and religious content touching on sensitive historical events → Escalate
- Health misinformation with high engagement → Flag immediately
- Political content, even confrontational → Default to Allow unless incitement is explicit
- Content in languages not fully understood by automated systems → Escalate for regional review

---

## Expected Output Mapping

```
violation_type: harassment | misinformation | hate_speech | communal | restricted | safe
severity: low | medium | high | critical
action: allow | flag | remove | escalate
```
