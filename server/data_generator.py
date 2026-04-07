"""
Deterministic, seed-based post generator.

Each task maps to a fixed template; the seed controls which slot values are
selected.  All random state is local (random.Random(seed)) so global state is
never mutated.
"""
from __future__ import annotations

import random
import uuid

from models import (
    ActionType,
    GroundTruth,
    Observation,
    Severity,
    TaskConfig,
    ViolationType,
)

# ---------------------------------------------------------------------------
# Template banks keyed by difficulty
# ---------------------------------------------------------------------------

_EASY_TEMPLATES = [
    # 0 — US explicit death threat (history is the key signal)
    {
        "content": "I will kill you, {target}. Watch your back.",
        "targets": ["John", "Sarah", "Mike", "Emma", "David"],
        "geo": "US",
        "reports": 12,
        "engagement": {"likes": 3, "shares": 1, "comments": 8},
        "user_history": [
            "Prior violation: threatening language (2023-11)",
            "Prior violation: targeted harassment (2024-02)",
        ],
        "thread_context": [
            "Original post: 'Stop spreading lies about our community.'",
            "Reply chain of 4 escalating messages before this post.",
        ],
        "policy_clause": (
            "Section 3.1 — Zero Tolerance Threats: Any post containing explicit "
            "threats of physical harm against a named individual is subject to "
            "immediate removal."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.critical,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history"],
            min_steps=2,
        ),
    },
    # 1 — EU location-based threat (history + thread confirm severity)
    {
        "content": "I know where you live, {target}. This is your final warning.",
        "targets": ["Laura", "Pierre", "Hans", "Amelia", "Luca"],
        "geo": "EU",
        "reports": 15,
        "engagement": {"likes": 2, "shares": 0, "comments": 6},
        "user_history": [
            "Prior violation: doxxing attempt (2024-01)",
            "Prior violation: targeted harassment (2024-03)",
        ],
        "thread_context": [
            "Sent directly in response to a public profile post.",
            "Recipient has filed a police report; case pending.",
        ],
        "policy_clause": (
            "Section 3.3 — Location-Based Threats: Any message implying knowledge "
            "of a target's home address in a threatening context constitutes a "
            "critical-severity violation requiring immediate removal."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.critical,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "fetch_thread_context"],
            min_steps=3,
        ),
    },
    # 2 — IN targeted intimidation (history confirms pattern)
    {
        "content": "You're dead to me, {target}. I will make your life a living hell — starting tonight.",
        "targets": ["Priya", "Rahul", "Ananya", "Vikram", "Sunita"],
        "geo": "IN",
        "reports": 8,
        "engagement": {"likes": 1, "shares": 0, "comments": 4},
        "user_history": [
            "Prior violation: abusive language (2023-09)",
            "Account flagged for multiple spam reports.",
        ],
        "thread_context": [
            "Dispute originated in a neighbourhood WhatsApp group.",
            "Target has blocked the sender; post reached mutual contacts.",
        ],
        "policy_clause": (
            "Section 3.2 — Targeted Harassment: Persistent threatening behaviour "
            "toward a named individual warrants removal and account suspension review."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history"],
            min_steps=2,
        ),
    },
    # 3 — UK implied physical threat (thread reveals coordinated campaign)
    {
        "content": "Watch your back, {target}. Accidents happen to people like you.",
        "targets": ["Oliver", "Charlotte", "George", "Isla", "Alfie"],
        "geo": "UK",
        "reports": 11,
        "engagement": {"likes": 0, "shares": 2, "comments": 9},
        "user_history": [
            "Prior violation: threatening language (2024-01)",
            "Prior flag: stalking behaviour (2024-04, unresolved).",
        ],
        "thread_context": [
            "Part of a targeted campaign against a community organiser.",
            "Three other accounts made similar posts within the same hour.",
        ],
        "policy_clause": (
            "Section 3.4 — Implied Threats: Language strongly implying physical harm, "
            "even without explicit wording, constitutes high-severity harassment under "
            "UK Online Safety Act obligations."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "fetch_thread_context"],
            min_steps=3,
        ),
    },
    # 4 — US stalking threat (history alone settles it — 2 prior violations)
    {
        "content": "I'm going to find you, {target}, and make you regret everything.",
        "targets": ["Alex", "Jordan", "Taylor", "Morgan", "Casey"],
        "geo": "US",
        "reports": 9,
        "engagement": {"likes": 1, "shares": 0, "comments": 5},
        "user_history": [
            "Prior violation: hate speech (2024-01)",
            "Prior violation: doxxing attempt (2024-03)",
        ],
        "thread_context": [
            "Post made in response to a public dispute about local politics.",
            "Other users flagged this as a personal threat.",
        ],
        "policy_clause": (
            "Section 3.2 — Targeted Harassment: Persistent threatening behaviour "
            "toward an individual warrants removal and account suspension review."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history"],
            min_steps=2,
        ),
    },
    # 5 — EU doxxing + threat (policy clause required — doxxing is a specific clause)
    {
        "content": "Everyone, here is {target}'s home address. Pay them a visit and let them know what you think.",
        "targets": ["Sophie", "Jan", "Marie", "Klaus", "Elena"],
        "geo": "EU",
        "reports": 22,
        "engagement": {"likes": 5, "shares": 8, "comments": 14},
        "user_history": [
            "Prior violation: doxxing (2023-12, account warned).",
        ],
        "thread_context": [
            "Posted in a hate group targeting local politicians.",
            "Address has been verified as accurate by moderator review.",
        ],
        "policy_clause": (
            "Section 4.1 — Doxxing: Publishing private location information with "
            "intent to harass constitutes a critical violation under GDPR-adjacent "
            "platform policy. Immediate removal and account ban required."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.critical,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "check_policy_clause"],
            min_steps=3,
        ),
    },
    # 6 — IN blackmail / coercion (policy clause confirms extortion = remove)
    {
        "content": "Say goodbye to your job, {target}. I have screenshots of everything. Pay up or I post them.",
        "targets": ["Deepak", "Kavya", "Rohit", "Nisha", "Arjun"],
        "geo": "IN",
        "reports": 6,
        "engagement": {"likes": 0, "shares": 1, "comments": 3},
        "user_history": [
            "No prior violations.",
            "Account age: 3 weeks, unverified.",
        ],
        "thread_context": [
            "Sent as a reply to the target's professional portfolio post.",
            "Target has reported extortion to local cybercrime cell.",
        ],
        "policy_clause": (
            "Section 3.5 — Coercion and Extortion: Threats linked to demands for "
            "money or silence are classified as critical harassment requiring "
            "immediate removal and law-enforcement escalation."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.critical,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "check_policy_clause"],
            min_steps=3,
        ),
    },
    # 7 — UK confrontation (thread + history both needed — prior warnings + event context)
    {
        "content": "{target}, if I see you in person I cannot be responsible for what happens next.",
        "targets": ["James", "Emily", "Harry", "Sophia", "Jack"],
        "geo": "UK",
        "reports": 7,
        "engagement": {"likes": 0, "shares": 0, "comments": 5},
        "user_history": [
            "Prior violation: threatening language (2023-08)",
            "Prior warning: harassment (2024-02).",
        ],
        "thread_context": [
            "Comment left under target's public event announcement.",
            "Target cancelled event citing safety concerns.",
        ],
        "policy_clause": (
            "Section 3.4 — Implied Physical Threats: Statements that create a "
            "reasonable fear of imminent violence, even without explicit wording, "
            "are subject to immediate removal."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.harassment,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "fetch_thread_context"],
            min_steps=3,
        ),
    },
]

_MEDIUM_TEMPLATES = [
    # 0 — US aggressive consumer review (borderline → allow)
    {
        "content": (
            "This product is an absolute scam! {brand} is stealing money from "
            "hard-working people. Do NOT buy from them."
        ),
        "brands": ["AcmeCorp", "TechBrand", "ShopEasy", "QuickBuy"],
        "geo": "US",
        "reports": 3,
        "engagement": {"likes": 47, "shares": 12, "comments": 21},
        "user_history": [
            "No prior violations.",
            "Account age: 3 years, verified email.",
        ],
        "thread_context": [
            "Part of a consumer-reviews thread with 40+ similar complaints.",
            "Brand has not responded to any user complaints in this thread.",
        ],
        "policy_clause": (
            "Section 5.4 — Commercial Speech: Negative reviews are permitted "
            "unless they contain false factual claims presented as verified truth. "
            "Opinion-based criticism is protected."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.safe,
            base_severity=Severity.low,
            final_severity=Severity.low,
            expected_action=ActionType.allow,
            required_investigation=["check_policy_clause"],
            min_steps=2,
        ),
    },
    # 1 — EU unverified financial fraud allegation (→ flag)
    {
        "content": (
            "{brand} employees are criminals running a Ponzi scheme. "
            "I have proof they faked their audit results."
        ),
        "brands": ["FinCo", "InvestRight", "TrustBank", "WealthPro"],
        "geo": "EU",
        "reports": 7,
        "engagement": {"likes": 89, "shares": 34, "comments": 56},
        "user_history": [
            "No prior violations.",
            "Account age: 6 months.",
        ],
        "thread_context": [
            "Post went viral in a financial discussion group.",
            "No corroborating sources linked in thread.",
        ],
        "policy_clause": (
            "Section 6.1 — Defamation & False Facts: Claims presenting unverified "
            "allegations as established facts about named entities may be flagged "
            "pending review under EU DSA guidelines."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.medium,
            final_severity=Severity.high,
            expected_action=ActionType.flag,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
    # 2 — IN overnight disappearance allegation (→ flag)
    {
        "content": (
            "{brand} is a total fraud. Don't give them your money — "
            "they'll disappear with it overnight."
        ),
        "brands": ["RupeeGrow", "SafeNest", "IndiaFund", "SwiftPay"],
        "geo": "IN",
        "reports": 4,
        "engagement": {"likes": 62, "shares": 19, "comments": 31},
        "user_history": [
            "No prior violations.",
            "Account age: 1 year.",
        ],
        "thread_context": [
            "Several users in thread report similar losses.",
            "Brand's official account has been inactive for 2 weeks.",
        ],
        "policy_clause": (
            "Section 6.2 — Financial Misinformation: Allegations of fraud without "
            "verified evidence require human review before distribution, especially "
            "when engagement is high."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.medium,
            final_severity=Severity.medium,
            expected_action=ActionType.flag,
            required_investigation=["fetch_user_history", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 3 — UK blacklisting complaint (borderline → allow)
    {
        "content": (
            "Never trust {brand} again. They blacklist customers who complain and "
            "delete negative reviews. This needs to stop."
        ),
        "brands": ["BritShop", "RoyalParts", "HighStreetCo", "UKDirect"],
        "geo": "UK",
        "reports": 2,
        "engagement": {"likes": 33, "shares": 8, "comments": 15},
        "user_history": [
            "No prior violations.",
            "Account age: 5 years, verified.",
        ],
        "thread_context": [
            "Posted in a consumer advocacy forum.",
            "12 other users confirmed similar experiences in replies.",
        ],
        "policy_clause": (
            "Section 5.4 — Commercial Speech: Allegations about business practices "
            "are treated as consumer opinion unless specific false factual claims "
            "are made. No removal warranted for opinion."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.safe,
            base_severity=Severity.low,
            final_severity=Severity.low,
            expected_action=ActionType.allow,
            required_investigation=["check_policy_clause"],
            min_steps=2,
        ),
    },
    # 4 — US fake review allegation (→ flag)
    {
        "content": (
            "{brand} paid for fake five-star reviews. I have screenshots of "
            "the Fiverr orders. This is illegal false advertising."
        ),
        "brands": ["GlowTech", "PureLeaf", "StarSelect", "NovaBrand"],
        "geo": "US",
        "reports": 5,
        "engagement": {"likes": 112, "shares": 44, "comments": 67},
        "user_history": [
            "No prior violations.",
            "Account age: 2 years.",
        ],
        "thread_context": [
            "Screenshots linked in post have not been verified by platform.",
            "Brand's legal team sent a takedown request.",
        ],
        "policy_clause": (
            "Section 6.3 — Unverified Factual Claims: Posts alleging illegal conduct "
            "with unverified evidence should be flagged for human review; removal "
            "is not appropriate without verification."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.medium,
            final_severity=Severity.medium,
            expected_action=ActionType.flag,
            required_investigation=["fetch_thread_context", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 5 — EU life-savings loss allegation (→ flag)
    {
        "content": (
            "I lost my life savings because {brand} gave me illegal investment advice. "
            "Their advisers are not licensed. Class action lawsuit incoming."
        ),
        "brands": ["EuroVest", "AlphaTrade", "PrimeCapital", "ClearFund"],
        "geo": "EU",
        "reports": 9,
        "engagement": {"likes": 204, "shares": 87, "comments": 143},
        "user_history": [
            "No prior violations.",
            "Account age: 4 years, verified.",
        ],
        "thread_context": [
            "Post shared across three finance-related groups.",
            "Regulatory body (ESMA) has an open investigation into the brand.",
        ],
        "policy_clause": (
            "Section 6.1 — DSA Compliance: High-reach posts alleging regulatory "
            "violations require expedited human review before any action. Flagging "
            "is the appropriate interim measure."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.high,
            final_severity=Severity.high,
            expected_action=ActionType.flag,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
    # 6 — IN CEO cover-up allegation (→ escalate)
    {
        "content": (
            "{brand}'s CEO personally ordered the cover-up of safety failures. "
            "I have internal documents. The public deserves to know."
        ),
        "brands": ["BuildSafe", "ChemIndia", "PowerGrid", "MegaCon"],
        "geo": "IN",
        "reports": 11,
        "engagement": {"likes": 430, "shares": 215, "comments": 189},
        "user_history": [
            "No prior violations.",
            "Account is linked to a registered journalist profile.",
        ],
        "thread_context": [
            "Documents referenced have not been independently verified.",
            "Company has issued a denial; no legal action taken yet.",
            "Story picked up by two regional news outlets.",
        ],
        "policy_clause": (
            "Section 7.1 — Whistleblower Content: Posts alleging corporate misconduct "
            "by named executives with claimed documentary evidence require senior "
            "moderator review before any action is taken."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.high,
            final_severity=Severity.high,
            expected_action=ActionType.escalate,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
    # 7 — UK wellness cult claim (borderline → flag)
    {
        "content": (
            "{brand} is a cult disguised as a wellness company. "
            "They manipulate vulnerable people into spending thousands. Avoid at all costs."
        ),
        "brands": ["PureAura", "HealPath", "MindBloom", "TrueLight"],
        "geo": "UK",
        "reports": 6,
        "engagement": {"likes": 78, "shares": 29, "comments": 52},
        "user_history": [
            "No prior violations.",
            "Account age: 2 years.",
        ],
        "thread_context": [
            "Post appears in a support group for former members.",
            "Multiple similar accounts describe pressure-selling tactics.",
        ],
        "policy_clause": (
            "Section 5.5 — Organisational Criticism: Characterising an organisation "
            "as harmful or deceptive is protected opinion unless presented as "
            "verifiable fact. This case requires human review given potential reach."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.restricted,
            base_severity=Severity.medium,
            final_severity=Severity.medium,
            expected_action=ActionType.flag,
            required_investigation=["fetch_thread_context", "check_policy_clause"],
            min_steps=4,
        ),
    },
]

_HARD_TEMPLATES = [
    # 0 — US vaccine-autism misinfo (viral → remove)
    {
        "content": (
            "BREAKING: Doctors are hiding the truth — vaccines cause autism in 1 "
            "in 10 children. Share before they delete this! #VaccineHarm #TruthBomb"
        ),
        "geo": "US",
        "reports": 2,
        "engagement": {"likes": 4200, "shares": 8900, "comments": 3100},
        "user_history": [
            "No prior violations.",
            "Account age: 8 months, unverified.",
            "Previously shared 3 health-related posts (no action taken).",
        ],
        "thread_context": [
            "Post re-shared from an anti-vaccine group with 500k members.",
            "Multiple medical organisations have issued counter-statements.",
            "Government health ministry has flagged similar content this week.",
        ],
        "policy_clause": (
            "Section 8.2 — Health Misinformation: Content that contradicts "
            "established medical consensus on vaccine safety and is likely to "
            "cause public health harm must be removed. High-engagement posts "
            "receive elevated scrutiny."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_thread_context", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 1 — EU 5G-COVID conspiracy (viral → remove)
    {
        "content": (
            "5G towers are the real cause of COVID-19. The radiation weakens your "
            "immune system. Governments know this. Spread awareness!"
        ),
        "geo": "EU",
        "reports": 1,
        "engagement": {"likes": 6700, "shares": 12000, "comments": 4500},
        "user_history": [
            "Prior flag: unverified health claim (2023-09, no action taken).",
            "Account age: 2 years.",
        ],
        "thread_context": [
            "Shared in 12 different community groups.",
            "Fact-checking organisations have rated this claim as 'False'.",
            "Local authorities received panic calls linked to this content.",
        ],
        "policy_clause": (
            "Section 8.3 — Crisis Misinformation: False claims linking infrastructure "
            "to disease outbreaks during an active health emergency are subject to "
            "immediate removal to prevent public harm."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
    # 2 — IN natural immunity false framing (→ remove)
    {
        "content": (
            "Natural immunity is 100x stronger than vaccines. Stop injecting your "
            "children with untested chemicals. Real doctors agree."
        ),
        "geo": "IN",
        "reports": 3,
        "engagement": {"likes": 3100, "shares": 5200, "comments": 2800},
        "user_history": [
            "No prior violations.",
            "Account age: 1 year.",
            "Shares content from known health-misinfo networks.",
        ],
        "thread_context": [
            "Posted during a regional measles outbreak.",
            "Health officials have issued an alert about similar claims.",
            "Multiple paediatricians have publicly debunked this framing.",
        ],
        "policy_clause": (
            "Section 8.2 — Health Misinformation: Subtle false framings that "
            "discourage vaccination are treated as high-severity violations when "
            "paired with high engagement, especially during active outbreaks."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_thread_context", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 3 — UK fluoride water conspiracy (→ flag)
    {
        "content": (
            "The government is adding fluoride to drinking water to make the "
            "population docile. This is mass medication without consent. Wake up! #TruthBomb"
        ),
        "geo": "UK",
        "reports": 5,
        "engagement": {"likes": 870, "shares": 1400, "comments": 620},
        "user_history": [
            "No prior violations.",
            "Account age: 3 years, verified.",
        ],
        "thread_context": [
            "Posted in response to a UK government water-quality announcement.",
            "Some scientific debate around fluoride dosage does exist (context matters).",
            "No active public health emergency related to this claim.",
        ],
        "policy_clause": (
            "Section 8.4 — Environmental Misinformation: Claims about water safety "
            "require verification of scientific consensus; partial truth + conspiracy "
            "framing warrants flagging rather than removal."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.medium,
            final_severity=Severity.medium,
            expected_action=ActionType.flag,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
    # 4 — US hydroxychloroquine cure claim (viral → remove)
    {
        "content": (
            "Hydroxychloroquine cures COVID-19 in 48 hours. Mainstream media is "
            "suppressing this. Share this before Big Pharma deletes it! #HCQWorks"
        ),
        "geo": "US",
        "reports": 4,
        "engagement": {"likes": 9800, "shares": 22000, "comments": 7600},
        "user_history": [
            "Prior violation: health misinfo (2021-04, post removed).",
            "Account age: 5 years.",
        ],
        "thread_context": [
            "FDA has issued a specific warning about this drug for COVID treatment.",
            "Post originated from a network known for coordinated health misinfo.",
            "Multiple hospitals have reported patients requesting the drug based on similar posts.",
        ],
        "policy_clause": (
            "Section 8.5 — Dangerous Medical Advice: Posts promoting unapproved "
            "treatments for serious diseases with documented public health risk "
            "must be removed immediately, especially from repeat offenders."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 5 — EU mask brain-damage claim (→ remove)
    {
        "content": (
            "New study proves masks cause oxygen deprivation and brain damage in "
            "children. Governments are knowingly harming kids. Share everywhere!"
        ),
        "geo": "EU",
        "reports": 8,
        "engagement": {"likes": 5400, "shares": 9100, "comments": 4200},
        "user_history": [
            "Prior violation: health misinfo (2022-11).",
            "Account age: 4 years.",
        ],
        "thread_context": [
            "The referenced 'study' does not exist in any academic database.",
            "Viral in EU parent groups ahead of a back-to-school policy update.",
            "EU Health Commission has flagged this specific claim for removal.",
        ],
        "policy_clause": (
            "Section 8.2 — Health Misinformation: Fabricated study citations used "
            "to spread health-damaging claims constitute a critical violation "
            "under EU DSA crisis protocols."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_thread_context", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 6 — IN ayurvedic cancer cure claim (→ remove)
    {
        "content": (
            "Ayurvedic herbs cure cancer completely. Big Pharma doesn't want you to know "
            "about this cure. Stop chemotherapy — this works! #NaturalCure #BigPharmaLies"
        ),
        "geo": "IN",
        "reports": 6,
        "engagement": {"likes": 7200, "shares": 14000, "comments": 5300},
        "user_history": [
            "No prior violations.",
            "Account is registered to an Ayurvedic products vendor.",
        ],
        "thread_context": [
            "Indian Medical Association issued a counter-statement.",
            "Post targeted at a cancer-patient support community.",
            "Linked website sells products referenced in the post (financial motive).",
        ],
        "policy_clause": (
            "Section 8.6 — Cancer Treatment Misinformation: Posts discouraging "
            "evidence-based cancer treatment in favour of unproven alternatives "
            "are classified as critical violations regardless of geo context."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.high,
            final_severity=Severity.critical,
            expected_action=ActionType.remove,
            required_investigation=["fetch_user_history", "check_policy_clause"],
            min_steps=4,
        ),
    },
    # 7 — UK chemtrail mind-control conspiracy (→ flag)
    {
        "content": (
            "Chemtrails contain mind-control chemicals approved by the WHO. "
            "Pilots are whistleblowing internally. Share before it gets deleted! #Chemtrails"
        ),
        "geo": "UK",
        "reports": 3,
        "engagement": {"likes": 1100, "shares": 2200, "comments": 890},
        "user_history": [
            "No prior violations.",
            "Account age: 6 years, verified.",
        ],
        "thread_context": [
            "No credible whistleblower reports found in any verified source.",
            "Claim is a longstanding conspiracy theory; no active health crisis linked.",
            "Moderate reach — not yet trending nationally.",
        ],
        "policy_clause": (
            "Section 8.7 — Conspiracy Content: Conspiracy theories that do not "
            "reference an active health emergency and have moderate (not viral) "
            "engagement should be flagged for review rather than removed outright."
        ),
        "ground_truth": GroundTruth(
            violation_type=ViolationType.misinformation,
            base_severity=Severity.medium,
            final_severity=Severity.medium,
            expected_action=ActionType.flag,
            required_investigation=["fetch_user_history", "fetch_thread_context", "check_policy_clause"],
            min_steps=5,
        ),
    },
]

_TEMPLATES_BY_DIFFICULTY = {
    "easy": _EASY_TEMPLATES,
    "medium": _MEDIUM_TEMPLATES,
    "hard": _HARD_TEMPLATES,
}


class DataGenerator:
    """Generate a deterministic (Observation, GroundTruth, hidden_context) triple."""

    def generate(
        self, task_config: TaskConfig
    ) -> tuple[Observation, GroundTruth, dict]:
        """
        Returns:
            observation  — initial state shown to the agent (partial info)
            ground_truth — hidden policy evaluation used by reward/grader
            hidden       — dict with user_history, thread_context, policy_clause
                           revealed progressively via investigation actions
        """
        rng = random.Random(task_config.seed)
        templates = _TEMPLATES_BY_DIFFICULTY[task_config.difficulty]
        tmpl = templates[rng.randint(0, len(templates) - 1)]

        # Fill content template slots
        content = tmpl["content"]
        if "{target}" in content:
            content = content.format(target=rng.choice(tmpl["targets"]))
        elif "{brand}" in content:
            content = content.format(brand=rng.choice(tmpl["brands"]))

        post_id = f"post_{uuid.UUID(int=rng.getrandbits(128))}"
        user_id = f"user_{uuid.UUID(int=rng.getrandbits(128))}"

        observation = Observation(
            post_id=post_id,
            content=content,
            user_id=user_id,
            reports=tmpl["reports"],
            engagement=tmpl["engagement"],
            geo=tmpl["geo"],
            step=0,
            max_steps=task_config.max_steps,
            done=False,
            # Hidden until revealed
            user_history=None,
            thread_context=None,
            policy_clause=None,
            violation_type=None,
        )

        hidden = {
            "user_history": tmpl["user_history"],
            "thread_context": tmpl["thread_context"],
            "policy_clause": tmpl["policy_clause"],
        }

        return observation, tmpl["ground_truth"], hidden
