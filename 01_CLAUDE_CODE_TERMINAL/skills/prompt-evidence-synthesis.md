# EVIDENCE SYNTHESIS PROMPTS
## Prompts for Pattern Analysis and Evidence Integration

---

## PROMPT 1: TIMELINE CONSTRUCTION

### Input
```
Build comprehensive timeline from the following sources:

**Documents:** [List document IDs or folder path]
**Date Range:** [Start - End]
**Key Events to Track:** [List specific events or themes]
**Cross-Reference Requirements:** [Related timelines to integrate]

Focus: Causation chain, knowledge timeline, decision-making sequence
```

### Expected Output
```markdown
# MASTER TIMELINE: [Case Name]
**Scope:** [Date range]
**Events:** [Count]
**Sources:** [Count]
**Confidence:** [X]%

## CRITICAL PATH
[15-20 most important events in chronological order with full source attribution]

## CAUSATION CHAIN VISUALIZATION
[Step-by-step sequence showing legal causation]

## CONTRADICTIONS REVEALED BY TIMELINE
[Temporal impossibilities, inconsistent claims]

## EVIDENCE GAPS IDENTIFIED
[Missing time periods, unexplained transitions]

**Quality Control:**
✓ Chronological accuracy: 100%
✓ All events sourced
✓ Cross-references verified
```

---

## PROMPT 2: PATTERN RECOGNITION

### Input
```
Analyze document set for recurring patterns:

**Document Set:** [Specification]
**Pattern Types:** [Behavioral/Communication/Temporal/Financial]
**Hypothesis:** [If testing specific pattern hypothesis]
**Minimum Occurrences:** [Threshold for pattern significance]

Deliverable: Pattern analysis with legal significance assessment
```

### Expected Output
```markdown
# PATTERN ANALYSIS REPORT

## PATTERN #1: [Pattern Name]
**Type:** [Behavioral/Communication/etc.]
**Frequency:** [X instances over Y timeframe]
**Confidence:** [X]%

### PATTERN DESCRIPTION
[Clear explanation of recurring behavior/theme]

### SPECIFIC INSTANCES
[Documented examples with sources]

### LEGAL SIGNIFICANCE
[How pattern impacts case - knowledge, intent, damages, etc.]

### STRATEGIC RECOMMENDATIONS
[How to use pattern in motion/trial/settlement]
```

---

## PROMPT 3: CONTRADICTION MATRIX

### Input
```
Identify contradictions across the following sources:

**Witness Statements:** [List]
**Documents:** [List]
**Expert Reports:** [List]

Contradiction Types: All (Internal, Cross-witness, Document vs. Testimony, Timeline)
Priority: Focus on contradictions material to [specific issue]
```

### Expected Output
```markdown
# CONTRADICTION ANALYSIS
**Total Contradictions:** [X]
**Critical:** [X] | **High:** [X] | **Moderate:** [X] | **Low:** [X]

## CRITICAL CONTRADICTION #1
**Type:** [Category]
**Severity:** CRITICAL
**Confidence:** [X]%

**Statement A:**
[Quote, source, date]

**Statement B:**
[Conflicting quote, source, date]

**Analysis:**
[Why this is material, impeachment value, strategic use]

**Recommended Actions:**
[Specific tactical steps]
```

---

## PROMPT 4: WITNESS CREDIBILITY COMPARATIVE ANALYSIS

### Input
```
Compare credibility across witnesses:

**Witnesses:** [List all fact witnesses]
**Factors:** [Consistency, corroboration, bias, demeanor, specificity]
**Purpose:** [Trial prep/settlement evaluation/deposition strategy]
```

### Expected Output
```markdown
# WITNESS CREDIBILITY COMPARISON

| Witness | Credibility Score | Key Strengths | Key Weaknesses | Trial Value |
|---------|-------------------|---------------|----------------|-------------|
| [Name]  | [X]/100          | [List]        | [List]         | [Rating]    |

## CREDIBILITY ANALYSIS: [Each Witness]
[Detailed multi-factor assessment per witness]

## STRATEGIC RECOMMENDATIONS
**Most Credible (Feature Prominently):** [Name]
**Least Credible (Impeach/Limit):** [Name]
**Wildcard (Prepare Thoroughly):** [Name]
```

---

## PROMPT 5: EVIDENCE GAP ANALYSIS

### Input
```
Identify gaps in evidence for proving:

**Elements to Prove:** [List legal elements]
**Evidence Available:** [Summary of current evidence]
**Discovery Status:** [% complete]

Deliverable: Gap analysis with recommended discovery actions
```

### Expected Output
```markdown
# EVIDENCE GAP ANALYSIS

## CRITICAL GAPS (Require Immediate Action)

### GAP #1: [Description]
**Element Affected:** [Which element of claim/defense]
**What We Have:** [Current evidence]
**What We Need:** [Specific missing evidence]
**Impact if Unfilled:** [HIGH/MODERATE/LOW]
**Discovery Actions:** [Specific RFPs, interrogatories, depositions]
**Likelihood of Obtaining:** [X]%
**Urgency:** [CRITICAL/HIGH/MODERATE]

## DISCOVERY PRIORITY MATRIX
[Ranked list of discovery actions by impact and feasibility]
```

---

## EVIDENCE SYNTHESIS QUALITY STANDARDS

### Pattern Recognition
- Minimum 3 instances for pattern identification
- Statistical significance if applicable
- Alternative explanations considered
- Confidence scoring required

### Contradiction Detection
- Severity assessment required
- Impeachment value quantified
- Strategic use guidance provided
- False positive minimization (<10%)

### Timeline Accuracy
- 100% chronological accuracy
- Every event sourced with specific citation
- Gaps explicitly identified
- Cross-verification completed

---

END EVIDENCE SYNTHESIS PROMPTS
