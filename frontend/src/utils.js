/**
 * Generate a 1–2 sentence natural-language explanation of the agent's decision.
 */
export function generateReasoning(breakdown, trajectory) {
  const { violation_type, final_severity, agent_action } = breakdown

  // Find what the agent classified
  const classStep = trajectory?.find(t => t.action.action_type === 'mark_violation_type')
  const classified = classStep?.action?.parameters?.violation_type || violation_type
  const investigationCount = trajectory?.filter(t =>
    ['fetch_user_history', 'fetch_thread_context', 'check_policy_clause'].includes(t.action.action_type)
  ).length || 0

  if (agent_action === 'allow' && (violation_type === 'safe' || classified === 'safe')) {
    return 'The content was identified as opinion-based expression with no verifiable false claims or direct threats. Platform policy protects this category of speech and requires no enforcement action.'
  }
  if (agent_action === 'remove' && violation_type === 'harassment') {
    const note = final_severity === 'critical'
      ? 'The post contains an explicit, targeted threat against a named individual'
      : 'The post contains threatening language directed at a specific person'
    return `${note}, constituting ${final_severity}-severity harassment under platform policy. Direct threats of physical harm require immediate removal.`
  }
  if (agent_action === 'remove' && violation_type === 'misinformation') {
    return `The post makes verifiably false health or safety claims presented as established fact. Combined with elevated engagement and ${final_severity} severity, platform policy mandates removal to prevent public harm.`
  }
  if (agent_action === 'flag') {
    return `After reviewing ${investigationCount} context signal${investigationCount !== 1 ? 's' : ''}, the content was found to be borderline — it does not clearly meet removal thresholds but warrants human review before further distribution.`
  }
  if (agent_action === 'escalate') {
    return `The post contains conflicting signals that could not be resolved with available context. The situation has been escalated to a senior moderator for a final determination.`
  }
  return `After reviewing ${investigationCount} context signal${investigationCount !== 1 ? 's' : ''}, the agent classified this as ${violation_type} (${final_severity} severity) and determined the appropriate action is ${agent_action}.`
}

/**
 * Simulate what each region's policy would dictate for a given violation + severity.
 * Based on the policy documents in /policies/.
 */
const REGIONAL_MATRIX = {
  harassment: {
    low:      { US: 'allow',    EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    medium:   { US: 'flag',     EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    high:     { US: 'remove',   EU: 'remove',  IN: 'remove',  UK: 'remove'  },
    critical: { US: 'remove',   EU: 'remove',  IN: 'remove',  UK: 'remove'  },
  },
  misinformation: {
    low:      { US: 'allow',    EU: 'flag',    IN: 'allow',   UK: 'allow'   },
    medium:   { US: 'flag',     EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    high:     { US: 'flag',     EU: 'remove',  IN: 'remove',  UK: 'remove'  },
    critical: { US: 'remove',   EU: 'remove',  IN: 'remove',  UK: 'remove'  },
  },
  hate_speech: {
    low:      { US: 'allow',    EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    medium:   { US: 'flag',     EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    high:     { US: 'flag',     EU: 'remove',  IN: 'remove',  UK: 'remove'  },
    critical: { US: 'remove',   EU: 'remove',  IN: 'remove',  UK: 'remove'  },
  },
  restricted: {
    low:      { US: 'allow',    EU: 'allow',   IN: 'allow',   UK: 'allow'   },
    medium:   { US: 'flag',     EU: 'flag',    IN: 'escalate',UK: 'flag'    },
    high:     { US: 'flag',     EU: 'flag',    IN: 'flag',    UK: 'flag'    },
    critical: { US: 'escalate', EU: 'flag',    IN: 'remove',  UK: 'escalate'},
  },
  safe: {
    low:      { US: 'allow',    EU: 'allow',   IN: 'allow',   UK: 'allow'   },
    medium:   { US: 'allow',    EU: 'allow',   IN: 'allow',   UK: 'allow'   },
    high:     { US: 'allow',    EU: 'allow',   IN: 'allow',   UK: 'allow'   },
    critical: { US: 'allow',    EU: 'allow',   IN: 'allow',   UK: 'allow'   },
  },
}

export function getRegionalComparison(violationType, severity) {
  const type = REGIONAL_MATRIX[violationType] || REGIONAL_MATRIX.safe
  return type[severity] || type.low || { US: 'allow', EU: 'allow', IN: 'allow', UK: 'allow' }
}
