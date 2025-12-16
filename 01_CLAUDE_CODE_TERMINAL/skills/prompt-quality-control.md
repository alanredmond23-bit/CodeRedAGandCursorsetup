# QUALITY CONTROL & FACT-CHECKING PROMPTS
## Prompts for Validation and Accuracy Verification

---

## PROMPT 1: CITATION VERIFICATION

### Input
```
Verify all citations in the following document:

**Document:** [Brief/Memo/Report]
**Citation Format Required:** [Bluebook/ALWD]

Check:
- Citation accuracy (case name, reporter, page)
- Still good law (Shepardize)
- Pinpoint citations match quoted text
- Subsequent history included
- Proper formatting
```

### Expected Output
```markdown
# CITATION VERIFICATION REPORT

## SUMMARY
**Total Citations:** [X]
**Verified Correct:** [X] ([%])
**Errors Found:** [X] ([%])
**Good Law Status:** [X pass / X fail]

## ERRORS IDENTIFIED

### ERROR #1 - Citation [X]
**Location in Document:** Page [X], footnote [X]
**As Written:** [Incorrect citation]
**Correct Citation:** [Corrected]
**Error Type:** [Case name misspelled/wrong page/etc.]
**Severity:** [CRITICAL/MODERATE/MINOR]

### ERROR #2 - Bad Law Warning
**Citation:** [Case citation]
**Status:** OVERRULED by [Case], [Year]
**Impact:** [CRITICAL - holding no longer valid]
**Replacement Authority:** [Alternative case]

## SHEPARD'S RESULTS
[Summary of treatment for each case]

## QUALITY SCORE: [X]/100
**Ready for Filing:** [YES/NO]
**Corrections Required:** [List]
```

---

## PROMPT 2: FACT-CHECKING AGAINST SOURCES

### Input
```
Verify all factual assertions in:

**Document:** [Brief/Declaration/Report]
**Source Documents:** [List of record documents]

Check: Every factual claim has source, quotes are accurate, inferences are supported
```

### Expected Output
```markdown
# FACT-CHECK REPORT

## VERIFICATION SUMMARY
**Total Factual Claims:** [X]
**Verified:** [X] ([%])
**Unable to Verify:** [X] ([%])
**Inaccuracies Found:** [X]

## VERIFICATION DETAILS

### CLAIM #1
**As Stated:** "[Factual assertion]"
**Source Cited:** [Document ID, page]
**Verification:** ✅ ACCURATE
**Confidence:** 99%

### CLAIM #2
**As Stated:** "[Assertion]"
**Source Cited:** [Document ID]
**Verification:** ❌ INACCURATE
**Actual Source Text:** "[What source actually says]"
**Discrepancy:** [Explanation]
**Severity:** [CRITICAL/MODERATE/MINOR]
**Correction Needed:** [Revised language]

## UNSUPPORTED ASSERTIONS
[Claims lacking source attribution - require citation or removal]

## RECOMMENDATION
[Approve as-is / Corrections required before filing]
```

---

## PROMPT 3: MATHEMATICAL VERIFICATION

### Input
```
Verify all calculations in:

**Document:** [Damages calculation/Settlement analysis/Budget]
**Calculations to Check:** [All / Specific sections]

Verify: Arithmetic accuracy, formula correctness, assumptions validity
```

### Expected Output
```markdown
# CALCULATION VERIFICATION REPORT

## ARITHMETIC ACCURACY
**Total Calculations:** [X]
**Correct:** [X] ([%])
**Errors:** [X]

## ERRORS IDENTIFIED

### CALCULATION ERROR #1
**Location:** [Page/Section]
**As Calculated:** [Incorrect result]
**Correct Calculation:** [Step-by-step correction]
**Impact:** [Dollar amount / % error]
**Severity:** [HIGH/MODERATE/LOW]

## FORMULA VERIFICATION
[Check that formulas used are appropriate for purpose]

## ASSUMPTION VALIDATION
[Review reasonableness of assumptions underlying calculations]

## CORRECTED TOTALS
**Original:** $[X]
**Corrected:** $[Y]
**Difference:** $[Z]

**Recommendation:** [Approve / Revise before use]
```

---

## PROMPT 4: CONSISTENCY CHECK ACROSS DOCUMENTS

### Input
```
Check consistency across:

**Documents:** [List - e.g., Complaint, Brief, Declaration]
**Focus:** [Facts, dates, amounts, legal theories]

Verify: No contradictions between our own documents
```

### Expected Output
```markdown
# CROSS-DOCUMENT CONSISTENCY CHECK

## CONSISTENCY ANALYSIS

### CONSISTENT ELEMENTS ✅
[List elements that match across documents]

### INCONSISTENCIES IDENTIFIED ⚠️

### INCONSISTENCY #1
**Element:** [e.g., Date of incident]
**Document A:** [Complaint states "March 15"]
**Document B:** [Declaration states "March 16"]
**Impact:** [CRITICAL - material fact inconsistency]
**Resolution Required:** [Determine correct date, amend documents]

## NARRATIVE CONSISTENCY
[Verify story told is consistent across all filings]

## LEGAL THEORY CONSISTENCY
[Ensure claims/defenses align across documents]

**Overall Consistency Score:** [X]/100
**Action Required:** [Corrections before filing / Acceptable as-is]
```

---

## PROMPT 5: DEADLINE & PROCEDURAL RULE COMPLIANCE

### Input
```
Verify compliance with:

**Document:** [Motion/Brief]
**Court:** [Jurisdiction]
**Rules:** [FRCP/State rules/Local rules]
**Deadline:** [Date]

Check: Page limits, formatting, required contents, filing deadline, service requirements
```

### Expected Output
```markdown
# PROCEDURAL COMPLIANCE CHECK

## RULES COMPLIANCE

### PAGE LIMIT
**Rule:** [X pages maximum]
**Actual:** [Y pages]
**Status:** [COMPLIANT / EXCEEDS LIMIT]

### FORMATTING REQUIREMENTS
- [ ] Font: [Required vs. Actual]
- [ ] Margins: [Required vs. Actual]
- [ ] Line spacing: [Required vs. Actual]
- [ ] Citations: [Format required]

### REQUIRED CONTENTS
- [ ] Table of Contents
- [ ] Table of Authorities
- [ ] Statement of Facts
- [ ] Legal Argument
- [ ] Conclusion
- [ ] Certificate of Service
- [ ] [Other requirements]

### DEADLINE COMPLIANCE
**Filing Deadline:** [Date, time]
**Current Date:** [Date]
**Days Remaining:** [X]
**Status:** [ON TIME / AT RISK / OVERDUE]

## NON-COMPLIANCE ISSUES
[List any violations with severity and correction needed]

**Ready for Filing:** [YES / NO - corrections needed]
```

---

## PROMPT 6: PRIVILEGE REVIEW VERIFICATION

### Input
```
Verify privilege review accuracy:

**Documents Reviewed:** [Count or set]
**Privilege Assertions:** [Count]
**Review Method:** [AI-assisted / Manual / Both]

Validate: Privilege assertions appropriate, no false negatives, descriptions adequate
```

### Expected Output
```markdown
# PRIVILEGE REVIEW VERIFICATION

## SAMPLE AUDIT RESULTS
**Sample Size:** [X documents] (Y% of total)
**Privilege Assertions Reviewed:** [X]
**False Positives:** [X] ([%])
**False Negatives:** [X] ([%])
**Accuracy Rate:** [%]

## FALSE POSITIVE REVIEW
[Documents marked privileged but shouldn't be]

## FALSE NEGATIVE REVIEW
[Documents NOT marked privileged but should be - CRITICAL]

## PRIVILEGE LOG ADEQUACY
[Are descriptions sufficient per FRCP 26(b)(5)?]

**Confidence in Privilege Review:** [X]%
**Recommendation:** [Approve / Additional review needed]
```

---

## PROMPT 7: EXPERT REPORT REVIEW

### Input
```
Quality check expert report:

**Expert:** [Name]
**Report Type:** [Initial/Rebuttal]
**Subject Matter:** [Topic]

Check: Qualifications, methodology, Daubert compliance, support for opinions, consistency with other evidence
```

### Expected Output
```markdown
# EXPERT REPORT QUALITY REVIEW

## QUALIFICATION ASSESSMENT
**Credentials:** [Adequate / Inadequate]
**Experience:** [Relevant / Questionable]
**Daubert Standard:** [Likely admissible / At risk]

## METHODOLOGY REVIEW
**Methodology Used:** [Description]
**Scientific Validity:** [Assessment]
**Reliability:** [HIGH/MODERATE/LOW]
**Peer Review:** [Available / Not available]
**Error Rate:** [Known / Unknown]

## OPINION SUPPORT
[Are opinions adequately supported by data/evidence?]

## CONSISTENCY CHECK
**With Our Other Evidence:** [Consistent / Conflicts]
**Internal Consistency:** [Consistent / Contradictory]

## DAUBERT CHALLENGE RISK
**Probability of Challenge:** [X]%
**Likelihood of Exclusion:** [X]%
**Vulnerable Areas:** [List]

## RECOMMENDATIONS
- [ ] Strengthen methodology section
- [ ] Obtain additional data
- [ ] Revise opinion on [specific point]
- [ ] Prepare for Daubert hearing

**Overall Quality Score:** [X]/100
**Trial Readiness:** [Ready / Needs improvement]
```

---

## QUALITY CONTROL STANDARDS

### Accuracy Targets
- Citation accuracy: >99.5%
- Fact verification: >98%
- Mathematical accuracy: 100%
- Cross-document consistency: 100%
- Procedural compliance: 100%

### Review Protocols
- **Three-Layer Review:**
  1. AI-assisted initial check
  2. Paralegal verification
  3. Attorney final approval

### Escalation Triggers
- Any "CRITICAL" error → Immediate attorney notification
- Deadline at risk → Same-day escalation
- Privilege false negative → URGENT escalation
- Bad law citation → Immediate correction required

### Confidence Scoring
- 95-100%: High confidence, minimal risk
- 85-94%: Good, but attorney spot-check recommended
- 70-84%: Moderate concerns, attorney review required
- <70%: Significant issues, full attorney review mandatory

---

END QUALITY CONTROL PROMPTS
