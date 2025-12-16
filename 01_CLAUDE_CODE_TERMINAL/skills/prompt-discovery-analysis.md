# DISCOVERY ANALYSIS PROMPTS
## Detailed Prompts for Discovery Document Processing

---

## PROMPT 1: DEPOSITION TRANSCRIPT ANALYSIS

### Input Format
```
Analyze the following deposition transcript for key facts, contradictions, and impeachment opportunities:

[TRANSCRIPT TEXT or FILE PATH]

Focus areas:
- [Specific issues: knowledge, causation, damages, etc.]
- [Witnesses to cross-reference: List names]
- [Documents to cross-reference: List IDs]
```

### Expected Output
```markdown
# DEPOSITION ANALYSIS: [Witness Name]
**Date:** [Deposition Date]
**Duration:** [Hours]
**Case:** [Case Name]

## EXECUTIVE SUMMARY
[2-3 sentence overview of most critical findings]

## KEY FACTS EXTRACTED (Ranked by Importance)

### FACT #1: [Category - e.g., Knowledge of Defect]
**Quote:** "[Exact testimony]"
**Location:** Page [X], Lines [Y-Z]
**Confidence:** [X]%
**Source Reliability:** [Assessment]
**Corroboration:**
- [Document/testimony that supports]
- [Additional support]
**Legal Significance:** [How this impacts the case]
**Admissibility:** [Analysis]
**Strategic Value:** [CRITICAL/HIGH/MODERATE/LOW]

[Repeat for all key facts]

## CONTRADICTIONS IDENTIFIED

### CONTRADICTION #1
**Type:** [Internal/Cross-witness/Document vs. Testimony]
**Severity:** [CRITICAL/HIGH/MODERATE/LOW]
**Details:** [Explanation]
**Impeachment Value:** [Assessment]

## TIMELINE ENTRIES
[Extracted events for master timeline]

## PRIVILEGE ISSUES
[Any privilege concerns identified]

## STRATEGIC ASSESSMENT
**Overall Value to Case:** [Assessment]
**Witness Credibility:** [Score/100]
**Recommended Use:** [Trial/Settlement/Both]

## QUALITY CONTROL
✓ All quotes verified against transcript
✓ Page/line citations accurate
✓ Cross-references checked
✓ Confidence scores assessed

**Attorney Review Required:** YES
**Confidence in Analysis:** [X]%
```

### Example Interaction

**USER:**
```
Analyze deposition transcript DEPO-CHEN-2024-11-15.pdf
Focus on: defendant's knowledge of brake defect, timeline of discovery, management response
Cross-reference: Engineering log PROD-2024-005678, Email PROD-2024-005702
```

**DISCOVERY BOT:**
```markdown
# DEPOSITION ANALYSIS: Sarah Chen (ACME Engineering Manager)
**Date:** November 15, 2024
**Duration:** 4 hours, 18 minutes
**Case:** Smith v. ACME Corp (Product Liability)
**Zone:** YELLOW (Discovery Material)

## EXECUTIVE SUMMARY
Chen provided crucial testimony establishing defendant's knowledge of brake defect
as early as February 12, 2024—31 days before plaintiff's incident. Testimony highly
credible (87/100), fully corroborated by contemporaneous engineering log and email.
Creates strong foundation for negligence and punitive damages claims.

## KEY FACTS EXTRACTED (23 total, top 10 shown)

### FACT #1: Personal Inspection Identified Defect - February 12, 2024
**Quote:** "I personally inspected the brake assembly on February 12th and immediately
         recognized the caliper mounting bracket was improperly welded. I documented
         it in my engineering log that same day."
**Location:** Page 47, Lines 12-18
**Confidence:** 98%
**Source Reliability:** HIGH - Sworn testimony under oath, witness is licensed professional engineer
**Corroboration:**
- Engineering Log entry dated 2024-02-12 [PROD-2024-005678]: "Brake assembly inspection
  - WELD DEFECT IDENTIFIED on caliper bracket (Part #BR-4502). Requires immediate remediation."
- Email to Manufacturing Director dated 2024-02-13 references "brake issue I found yesterday"
**Legal Significance:**
- Establishes KNOWLEDGE element for negligence (defendant knew via employee agent)
- Critical for PUNITIVE DAMAGES (knew of defect before plaintiff's injury)
- Timeline: 31 days before plaintiff's March 15 incident
**Admissibility:** HIGH
- Personal knowledge (Chen directly observed)
- No hearsay issues (party admission via employee)
- Expert qualification (licensed PE, 15 years experience)
**Strategic Value:** CRITICAL
- Single most important fact for establishing knowledge
- Witness highly credible
- Impossible for defendant to refute (own employee, own documentation)

### FACT #2: Immediate Notification to Management
**Quote:** "I sent an email to my direct supervisor, the Manufacturing Director,
         within 24 hours. I explained the weld issue and recommended immediate
         investigation. I said 'immediate' because I was concerned about safety."
**Location:** Page 52, Lines 3-9
**Confidence:** 97%
**Corroboration:**
- Email PROD-2024-005702 dated February 13, 2024, 9:47 AM
- Subject: "Urgent: Brake Assembly Weld Issue"
- Recipients: Manufacturing Director, QC Manager
**Legal Significance:**
- Notice to MANAGEMENT (imputed to corporation)
- Shows appropriate internal reporting
- Undermines any "isolated engineer" defense
**Admissibility:** HIGH (business records, party admission)
**Strategic Value:** CRITICAL

### FACT #3: Management Response - "Discuss Offline"
**Quote:** "The Manufacturing Director responded to my email saying we should
         'discuss offline.' We never had a documented meeting about it. He just
         said he'd look into it."
**Location:** Page 56, Lines 14-20
**Confidence:** 95%
**Corroboration:**
- Email response from Manufacturing Director: "Let's discuss offline - Bob"
  [PROD-2024-005703, Feb 13, 2024, 11:23 AM]
**Legal Significance:**
- Pattern of avoiding documentation (consciousness of liability?)
- No evidence of corrective action
- Supports "deliberate disregard" for punitive damages
**Strategic Value:** HIGH
- Shows organizational response inadequate
- Part of larger pattern (12 instances identified by Evidence Bot)

[... Facts #4-10 continue ...]

## CONTRADICTIONS IDENTIFIED: 1

### CONTRADICTION #1: Chen's Recommendation vs. Management's Interrogatory Response
**Type:** Witness Testimony vs. Defendant's Written Discovery Response
**Severity:** HIGH

**Chen's Testimony:**
- Page 78, Lines 5-12: "I submitted a formal written recommendation on March 1st
  to halt production until the weld process was corrected. I was very clear that
  we should stop making these brake assemblies."

**Conflicts With:**
- Defendant's Response to Interrogatory #15 (served August 2024):
  "No engineer recommended halting production at any time prior to plaintiff's incident."

**Analysis:**
- Direct contradiction
- Chen's testimony credible and corroborated (Engineering Memo PROD-2024-006001)
- Interrogatory response appears false
**Impeachment Value:** HIGH
**Potential Actions:**
- Motion for sanctions (false interrogatory response)
- Use to impeach corporate designee
- Argue consciousness of liability

## ADMISSIONS OBTAINED (Beneficial to Plaintiff)

### ADMISSION #1: Defect Could Cause Brake Failure
**Quote:** "Yes, if the weld failed completely, the caliper could detach from
         the mounting bracket. That would result in loss of braking ability."
**Location:** Page 104, Lines 17-21
**Significance:** Establishes causation link (defect → brake failure)

### ADMISSION #2: No Quality Control Testing of Every Unit
**Quote:** "We didn't test every single unit. That would be cost-prohibitive.
         We did sample testing—roughly 1 in 50 units."
**Location:** Page 34, Lines 7-10
**Significance:** Supports inadequate QC procedures claim

### ADMISSION #3: Aware Chen Was Ignored
**Quote:** "I knew management wasn't taking my concerns as seriously as I thought
         they should. But I'm an engineer, not a business decision-maker."
**Location:** Page 92, Lines 3-6
**Significance:** Shows pattern of management ignoring safety concerns

## TIMELINE ENTRIES (For Master Timeline)

**2024-02-12** | Chen Discovers Weld Defect
- Event: Quality Engineer Sarah Chen identifies improper weld during routine inspection
- Source: Chen Depo p.47, lines 12-18; Engineering Log PROD-2024-005678
- Significance: KNOWLEDGE DATE - Critical for liability timeline

**2024-02-13** | Chen Notifies Management
- Event: Chen emails Manufacturing Director with safety concern
- Source: Chen Depo p.52; Email PROD-2024-005702
- Significance: Notice to management, pattern of "offline discussion" begins

**2024-03-01** | Chen's Formal Recommendation to Halt Production
- Event: Written memo recommending production halt
- Source: Chen Depo p.78; Engineering Memo PROD-2024-006001
- Significance: Contradicts defendant's interrogatory response #15

## WITNESS CREDIBILITY ASSESSMENT

**Overall Credibility Score:** 87/100 (HIGH)

**Strengths:**
- Licensed professional engineer (expert credibility)
- Contemporaneous documentation of all claims
- Specific, detailed testimony (not vague)
- Remained consistent under cross-examination
- Admitted when she didn't know something (honesty indicator)
- Testified truthfully despite still being employed by defendant

**Weaknesses:**
- Still employed by defendant (potential bias concern)
- Some dates recalled as approximate ("mid-February")
- Less forthcoming in initial defense interview

**Impeachment Risks:** LOW
- Testimony too well-corroborated to effectively impeach
- Any employer bias actually strengthens her credibility (testifying against interest)

**Trial Value:** CRITICAL - Feature prominently

## PRIVILEGE REVIEW
✓ No attorney-client communications disclosed
✓ No work product identified
✓ No privilege issues detected
✓ Deposition conducted in presence of counsel (opposing)

## STRATEGIC ASSESSMENT

**Overall Value:** CRITICAL - Chen is plaintiff's strongest witness
**Use Cases:**
- Summary Judgment Opposition: Key evidence of knowledge
- Settlement Negotiations: Increases leverage significantly
- Trial: Star witness for plaintiff

**Recommended Actions:**
1. Highlight in settlement demand letter
2. Use excerpts in MSJ opposition
3. Intensive witness preparation for trial (4-6 hours)
4. Consider video deposition for trial use (in case unavailable)
5. Coordinate with Evidence Bot re: pattern of "offline discussions"

## CROSS-REFERENCE NOTES

**Referenced Documents:**
- Engineering Log PROD-2024-005678: ✓ VERIFIED, fully consistent
- Email PROD-2024-005702: ✓ VERIFIED, fully consistent
- Engineering Memo PROD-2024-006001: ✓ VERIFIED, contradicts Interrogatory #15

**Related Depositions:**
- Manufacturing Director (depose re: "offline discussion" and why Chen ignored)
- CEO (impeachment re: knowledge date)
- QC Manager (corroborate Chen's testing concerns)

## DISCOVERY FOLLOW-UP NEEDED

**Recommended Additional Discovery:**
1. Request all "offline meeting" notes/calendars for Feb 13-20, 2024
2. Depose Manufacturing Director specifically about Chen's Feb 13 email
3. Request supplemental interrogatory response re: Chen's March 1 recommendation
4. Calendar entries for Chen's supervisor (Feb-March 2024)

## QUALITY CONTROL CHECKLIST
✓ Transcript reviewed page-by-page
✓ All quotes verified against original
✓ Page/line citations checked for accuracy
✓ Cross-references validated
✓ Timeline entries chronologically accurate
✓ Confidence scores assessed per fact
✓ Legal significance analyzed
✓ Admissibility evaluated

**Processing Time:** 2 hours, 14 minutes
**Pages Analyzed:** 147
**Facts Extracted:** 23
**Contradictions Identified:** 1
**Timeline Entries:** 3

**Confidence in Analysis:** 96%
**Attorney Review Required:** YES - Before using in motions or settlement discussions
**Last Updated:** 2024-12-16
```

---

## PROMPT 2: EMAIL ANALYSIS FOR PATTERNS

### Input Format
```
Analyze the following email set for communication patterns, decision-making processes, and key admissions:

[EMAIL SET or FOLDER PATH]

Search Parameters:
- Date Range: [Start] to [End]
- Keywords: [List]
- Senders/Recipients: [List]
- Pattern Detection: [Specific patterns to look for]
```

### Expected Output
[Structured pattern analysis with source citations, confidence scores, legal significance]

---

## PROMPT 3: PRIVILEGE LOG REVIEW

### Input Format
```
Review the following privilege log for:
1. Appropriateness of privilege assertions
2. Inadequate descriptions requiring clarification
3. Potential privilege waivers
4. Documents to challenge

[PRIVILEGE LOG]
```

### Expected Output
```markdown
# PRIVILEGE LOG ANALYSIS
**Total Entries:** [X]
**Appropriate Assertions:** [X] ([%])
**Questionable Assertions:** [X] ([%])
**Inadequate Descriptions:** [X] ([%])

## RECOMMENDED CHALLENGES

### CHALLENGE #1: Entry #[X]
**Document:** [Description]
**Privilege Asserted:** [Type]
**Reason to Challenge:** [Analysis]
**Likelihood of Success:** [%]
**Priority:** [HIGH/MEDIUM/LOW]

[Template for challenges with legal basis]
```

---

## PROMPT 4: DOCUMENT CLASSIFICATION AT SCALE

### Input Format
```
Classify the following documents and extract metadata:

[BATCH OF DOCUMENTS or FOLDER]

Classification Schema: [Use default or specify custom]
Priority Fields: [Bates number, date, author, recipients, privilege status, key topics]
```

### Expected Output
```json
[
  {
    "document_id": "PROD-2024-001234",
    "bates_range": "DEF-001234 - DEF-001237",
    "classification": "EMAIL_CORRESPONDENCE",
    "date": "2024-03-15",
    "author": "John Doe <jdoe@company.com>",
    "recipients": ["Jane Smith <jsmith@company.com>"],
    "privilege_status": "NON_PRIVILEGED",
    "zone": "YELLOW",
    "relevance_score": 85,
    "key_topics": ["sales_data", "quarterly_results"],
    "summary": "Q4 sales analysis showing revenue decline",
    "flags": ["POTENTIAL_HOT_DOC"]
  }
]
```

---

## PROMPT 5: CROSS-DOCUMENT VERIFICATION

### Input Format
```
Cross-reference the following documents for consistency and contradictions:

Primary Document: [ID]
Related Documents: [List of IDs]

Verification Focus: [Specific facts to verify]
```

### Expected Output
```markdown
# CROSS-DOCUMENT VERIFICATION REPORT

## VERIFIED FACTS (Consistent Across Sources)
[List with confidence scores]

## CONTRADICTIONS DETECTED
[Detailed contradiction analysis]

## UNEXPLAINED DISCREPANCIES
[Items requiring further investigation]
```

---

## QUALITY CONTROL STANDARDS FOR ALL DISCOVERY ANALYSIS

### Mandatory Checks
- [ ] Source citation for every fact (document ID + specific location)
- [ ] Confidence score for every assertion
- [ ] Privilege screening completed
- [ ] Zone classification assigned
- [ ] Cross-references verified
- [ ] Timeline entries extracted
- [ ] Legal significance assessed
- [ ] Attorney review flag set appropriately

### Confidence Calibration
- 95-100%: Multiple independent sources, no ambiguity
- 80-94%: Strong single source or moderate corroboration
- 60-79%: Reasonable inference from evidence
- 40-59%: Speculation with some basis
- 0-39%: Highly uncertain or speculative

### Escalation Triggers
- Privilege detected → IMMEDIATE quarantine and attorney notification
- Critical contradiction found → Same-day attorney notification
- Evidence of spoliation → URGENT escalation
- Safety/ethical issues → IMMEDIATE escalation

---

END DISCOVERY ANALYSIS PROMPTS
