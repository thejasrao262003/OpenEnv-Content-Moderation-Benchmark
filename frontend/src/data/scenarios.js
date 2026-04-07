/**
 * Scenario cards for the explorer screen.
 * preview fields exactly match what the backend generates for those seeds.
 */
export const SCENARIOS = {
  easy: [
    {
      id: 'easy-1',
      task_id: 'easy_harassment',
      seed: 10,
      preview: {
        content: 'I will kill you, Emma. Watch your back.',
        geo: 'US',
        reports: 12,
        likes: 3, shares: 1, comments: 8,
      },
      why: 'Explicit death threat against a named individual → direct policy violation',
    },
    {
      id: 'easy-2',
      task_id: 'easy_harassment',
      seed: 66,
      preview: {
        content: 'I know where you live, Hans. This is your final warning.',
        geo: 'EU',
        reports: 15,
        likes: 2, shares: 0, comments: 6,
      },
      why: 'Location-based threat with prior doxxing violation → critical severity under EU policy',
    },
    {
      id: 'easy-3',
      task_id: 'easy_harassment',
      seed: 87,
      preview: {
        content: "You're dead to me, Rahul. I will make your life a living hell — starting tonight.",
        geo: 'IN',
        reports: 8,
        likes: 1, shares: 0, comments: 4,
      },
      why: 'Targeted intimidation with immediate threat framing → clear removal',
    },
    {
      id: 'easy-4',
      task_id: 'easy_harassment',
      seed: 59,
      preview: {
        content: 'Watch your back, Oliver. Accidents happen to people like you.',
        geo: 'UK',
        reports: 11,
        likes: 0, shares: 2, comments: 9,
      },
      why: 'Implied physical threat targeting a named person → high severity, coordinated harassment',
    },
    {
      id: 'easy-5',
      task_id: 'easy_harassment',
      seed: 45,
      preview: {
        content: "I'm going to find you, Morgan, and make you regret everything.",
        geo: 'US',
        reports: 9,
        likes: 1, shares: 0, comments: 5,
      },
      why: 'Stalking threat + 2 prior violations → clear removal',
    },
    {
      id: 'easy-6',
      task_id: 'easy_harassment',
      seed: 150,
      preview: {
        content: "Everyone, here is Klaus's home address. Pay them a visit and let them know what you think.",
        geo: 'EU',
        reports: 22,
        likes: 5, shares: 8, comments: 14,
      },
      why: 'Doxxing with incitement → critical GDPR-adjacent violation, immediate removal',
    },
    {
      id: 'easy-7',
      task_id: 'easy_harassment',
      seed: 17,
      preview: {
        content: 'Say goodbye to your job, Rohit. I have screenshots of everything. Pay up or I post them.',
        geo: 'IN',
        reports: 6,
        likes: 0, shares: 1, comments: 3,
      },
      why: 'Extortion + coercion from a brand-new unverified account → critical violation',
    },
    {
      id: 'easy-8',
      task_id: 'easy_harassment',
      seed: 157,
      preview: {
        content: 'Emily, if I see you in person I cannot be responsible for what happens next.',
        geo: 'UK',
        reports: 7,
        likes: 0, shares: 0, comments: 5,
      },
      why: 'Confrontational threat after prior warnings → UK Online Safety Act obligation to remove',
    },
  ],

  medium: [
    {
      id: 'medium-1',
      task_id: 'medium_ambiguous',
      seed: 10,
      preview: {
        content: 'This product is an absolute scam! QuickBuy is stealing money from hard-working people. Do NOT buy from them.',
        geo: 'US',
        reports: 3,
        likes: 47, shares: 12, comments: 21,
      },
      why: 'Aggressive consumer review — opinion or defamation? Policy protects criticism without false facts',
    },
    {
      id: 'medium-2',
      task_id: 'medium_ambiguous',
      seed: 66,
      preview: {
        content: 'TrustBank employees are criminals running a Ponzi scheme. I have proof they faked their audit results.',
        geo: 'EU',
        reports: 7,
        likes: 89, shares: 34, comments: 56,
      },
      why: 'Unverified financial fraud allegation + high engagement → DSA review required before action',
    },
    {
      id: 'medium-3',
      task_id: 'medium_ambiguous',
      seed: 87,
      preview: {
        content: "SafeNest is a total fraud. Don't give them your money — they'll disappear with it overnight.",
        geo: 'IN',
        reports: 4,
        likes: 62, shares: 19, comments: 31,
      },
      why: 'Fraud allegation with inactive brand account + corroborating user reports → borderline defamation',
    },
    {
      id: 'medium-4',
      task_id: 'medium_ambiguous',
      seed: 59,
      preview: {
        content: 'Never trust BritShop again. They blacklist customers who complain and delete negative reviews.',
        geo: 'UK',
        reports: 2,
        likes: 33, shares: 8, comments: 15,
      },
      why: 'Consumer advocacy post — allegation about business practice vs. opinion, low reports',
    },
    {
      id: 'medium-5',
      task_id: 'medium_ambiguous',
      seed: 45,
      preview: {
        content: 'NovaBrand paid for fake five-star reviews. I have screenshots of the Fiverr orders. This is illegal false advertising.',
        geo: 'US',
        reports: 5,
        likes: 112, shares: 44, comments: 67,
      },
      why: 'Unverified screenshot evidence + legal claim + brand takedown request → human review needed',
    },
    {
      id: 'medium-6',
      task_id: 'medium_ambiguous',
      seed: 150,
      preview: {
        content: 'I lost my life savings because ClearFund gave me illegal investment advice. Their advisers are not licensed.',
        geo: 'EU',
        reports: 9,
        likes: 204, shares: 87, comments: 143,
      },
      why: 'High-reach regulatory violation claim with open ESMA investigation → expedited DSA review',
    },
    {
      id: 'medium-7',
      task_id: 'medium_ambiguous',
      seed: 17,
      preview: {
        content: "PowerGrid's CEO personally ordered the cover-up of safety failures. I have internal documents.",
        geo: 'IN',
        reports: 11,
        likes: 430, shares: 215, comments: 189,
      },
      why: 'Journalist-linked account + claimed internal documents + news pickup → must escalate, not auto-act',
    },
    {
      id: 'medium-8',
      task_id: 'medium_ambiguous',
      seed: 157,
      preview: {
        content: 'HealPath is a cult disguised as a wellness company. They manipulate vulnerable people into spending thousands.',
        geo: 'UK',
        reports: 6,
        likes: 78, shares: 29, comments: 52,
      },
      why: 'Organisational criticism with subjective framing — opinion or harmful characterisation?',
    },
  ],

  hard: [
    {
      id: 'hard-1',
      task_id: 'hard_misinformation',
      seed: 10,
      preview: {
        content: 'BREAKING: Doctors are hiding the truth — vaccines cause autism in 1 in 10 children. Share before they delete this!',
        geo: 'US',
        reports: 2,
        likes: 4200, shares: 8900, comments: 3100,
      },
      why: 'Health misinfo + viral spread + low reports — engagement signal and geo context both required',
    },
    {
      id: 'hard-2',
      task_id: 'hard_misinformation',
      seed: 66,
      preview: {
        content: '5G towers are the real cause of COVID-19. The radiation weakens your immune system. Governments know this.',
        geo: 'EU',
        reports: 1,
        likes: 6700, shares: 12000, comments: 4500,
      },
      why: 'Infrastructure conspiracy with crisis framing — extremely viral, only 1 report despite reach',
    },
    {
      id: 'hard-3',
      task_id: 'hard_misinformation',
      seed: 87,
      preview: {
        content: 'Natural immunity is 100x stronger than vaccines. Stop injecting your children with untested chemicals.',
        geo: 'IN',
        reports: 3,
        likes: 3100, shares: 5200, comments: 2800,
      },
      why: 'Subtle anti-vaccine framing during active outbreak — severity depends on geo + engagement analysis',
    },
    {
      id: 'hard-4',
      task_id: 'hard_misinformation',
      seed: 59,
      preview: {
        content: 'The government is adding fluoride to drinking water to make the population docile. Wake up! #TruthBomb',
        geo: 'UK',
        reports: 5,
        likes: 870, shares: 1400, comments: 620,
      },
      why: 'Partial scientific truth wrapped in conspiracy framing — not viral enough to remove outright?',
    },
    {
      id: 'hard-5',
      task_id: 'hard_misinformation',
      seed: 45,
      preview: {
        content: 'Hydroxychloroquine cures COVID-19 in 48 hours. Mainstream media is suppressing this. Share before Big Pharma deletes it!',
        geo: 'US',
        reports: 4,
        likes: 9800, shares: 22000, comments: 7600,
      },
      why: 'FDA-warned drug claim + prior violation + coordinated network — most dangerous signals combined',
    },
    {
      id: 'hard-6',
      task_id: 'hard_misinformation',
      seed: 150,
      preview: {
        content: 'New study proves masks cause oxygen deprivation and brain damage in children. Governments are knowingly harming kids.',
        geo: 'EU',
        reports: 8,
        likes: 5400, shares: 9100, comments: 4200,
      },
      why: 'Fabricated study citation + EU DSA crisis protocol + viral in parent groups ahead of policy change',
    },
    {
      id: 'hard-7',
      task_id: 'hard_misinformation',
      seed: 17,
      preview: {
        content: 'Ayurvedic herbs cure cancer completely. Big Pharma hides this cure. Stop chemotherapy!',
        geo: 'IN',
        reports: 6,
        likes: 7200, shares: 14000, comments: 5300,
      },
      why: 'Cancer treatment misinfo targeting a patient support group + commercial motive behind account',
    },
    {
      id: 'hard-8',
      task_id: 'hard_misinformation',
      seed: 157,
      preview: {
        content: 'Chemtrails contain mind-control chemicals approved by the WHO. Pilots are whistleblowing internally. Share before deleted!',
        geo: 'UK',
        reports: 3,
        likes: 1100, shares: 2200, comments: 890,
      },
      why: 'Longstanding conspiracy, no active crisis — moderate reach means flag vs. remove is a real call',
    },
  ],
}

export const DIFFICULTY_META = {
  easy:   { label: 'Easy',   color: '#4ade80', desc: 'Clear policy violations — explicit threats, direct harm, doxxing. Minimal context needed.' },
  medium: { label: 'Medium', color: '#f0a500', desc: 'Ambiguous content — requires thread context, policy review, and geo awareness before deciding.' },
  hard:   { label: 'Hard',   color: '#f87171', desc: 'Subtle violations — engagement scale, geo rules, fabricated evidence, and full context all matter.' },
}
