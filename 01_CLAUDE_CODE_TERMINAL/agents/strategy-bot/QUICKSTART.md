# Legal Strategy Bot - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /path/to/strategy-bot
pip install -r requirements.txt
```

### Step 2: Configure API Keys

Create a `.env` file:

```bash
# .env file
WESTLAW_API_KEY=your_westlaw_key_here
LEXISNEXIS_API_KEY=your_lexis_key_here
```

Or set environment variables:

```bash
export WESTLAW_API_KEY="your_westlaw_key_here"
export LEXISNEXIS_API_KEY="your_lexis_key_here"
```

### Step 3: Run Example

```python
from strategy_bot_main import LegalStrategyBot, CaseFacts, CaseType, Jurisdiction

# Initialize
bot = LegalStrategyBot()

# Simple custody case
case = CaseFacts(
    case_type=CaseType.CUSTODY,
    jurisdiction=Jurisdiction.STATE_CA,
    facts_summary="Father seeking custody modification due to mother's substance abuse",
    parties={'petitioner': 'John Doe', 'respondent': 'Jane Doe'},
    key_dates={'separation': '2021-01-01'},
    legal_issues=['Best interests of child', 'Substance abuse'],
    desired_outcome='Primary custody to father'
)

# Analyze
output = bot.analyze_case(case)

# Generate memo
memo = bot.generate_memo(output)
print(memo)
```

## What You Get

After running the analysis, you'll receive:

1. **JSON Output File**: `strategy_output_[CASE_ID].json`
   - Complete analysis data
   - All legal theories
   - Citation information
   - Confidence scores

2. **Legal Memorandum**: `legal_memo_[CASE_ID].txt`
   - Formatted legal memo
   - Theory analysis
   - Strategy recommendations
   - Counter-arguments
   - Settlement options

## Key Outputs Explained

### Confidence Scores

- **85%+**: Very strong - aggressive litigation
- **70-84%**: Strong - proceed confidently
- **50-69%**: Moderate - proceed cautiously
- **Below 50%**: Weak - reconsider strategy

### Legal Theories

Each theory includes:
- Theory name
- Supporting cases (with citations)
- Confidence score
- Strengths and weaknesses
- Counter-arguments

### Recommended Strategy

Based on confidence scores:
- Primary theory to pursue
- Alternative theories
- Motion strategy
- Settlement recommendations
- Timeline and resources

## Common Use Cases

### Custody Case

```python
case = CaseFacts(
    case_type=CaseType.CUSTODY,
    jurisdiction=Jurisdiction.STATE_CA,
    facts_summary="[Your facts]",
    legal_issues=['Best interests', 'Changed circumstances'],
    desired_outcome='Primary custody'
)
```

### Federal Criminal

```python
case = CaseFacts(
    case_type=CaseType.FEDERAL_CRIMINAL,
    jurisdiction=Jurisdiction.FEDERAL,
    facts_summary="[Your facts]",
    legal_issues=['Sentencing guidelines', 'Downward variance'],
    desired_outcome='Below guidelines sentence'
)
```

### Civil Litigation

```python
case = CaseFacts(
    case_type=CaseType.CIVIL_LITIGATION,
    jurisdiction=Jurisdiction.STATE_NY,
    facts_summary="[Your facts]",
    legal_issues=['Contract breach', 'Damages'],
    desired_outcome='Judgment for plaintiff'
)
```

## API Key Setup

### Westlaw Edge

1. Go to: https://developer.thomson.reuters.com/
2. Create account
3. Request API access
4. Copy API key
5. Set in environment or `.env` file

### LexisNexis

1. Go to: https://developer.lexisnexis.com/
2. Create account
3. Request API access
4. Copy API key
5. Set in environment or `.env` file

### No API Keys?

The system will use mock data for demonstration:
- Example cases from common legal issues
- Simulated citations
- Realistic outputs for testing

**Warning**: Mock data is for testing only. Do not use in actual cases.

## Validating Citations

Always validate citations before filing:

```python
from validation import CitationValidator

validator = CitationValidator(westlaw, lexis)

# Validate all
all_valid = validator.validate_all(cases)

# Get detailed report
report = validator.generate_validation_report(cases)
print(report)
```

## Generating Motions

```python
from motion_drafter import MotionDrafter

drafter = MotionDrafter()
strategy = drafter.generate_strategy(theories, case_facts)
motion = strategy['primary_motion_draft']

# Save to file
complete_motion = drafter.generate_complete_motion_document(motion)
with open('motion.txt', 'w') as f:
    f.write(complete_motion)
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in correct directory
cd /path/to/strategy-bot

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### API Connection Issues

```python
# Test connection
from westlaw_research import WestlawResearcher

westlaw = WestlawResearcher(api_key="your_key")
results = westlaw.search("test", max_results=1)
print(f"Connected: {len(results) >= 0}")
```

### No Results Found

- Check jurisdiction matches your case
- Broaden search terms
- Increase max_results parameter
- Verify API quota not exceeded

## Best Practices

### 1. Detailed Facts

Provide comprehensive fact summary:
- Key dates
- Parties involved
- Procedural history
- Relevant evidence
- Opposing arguments (if known)

### 2. Specific Legal Issues

List precise legal issues:
- ✓ "Best interests of child under Cal. Fam. Code § 3011"
- ✗ "Custody issues"

### 3. Review All Outputs

- Check every citation independently
- Verify Shepard's treatment
- Review counter-arguments
- Assess confidence scores critically

### 4. Attorney Review Required

**NEVER** file documents without attorney review:
- Legal judgment required
- Jurisdiction-specific rules
- Ethical obligations
- Client-specific strategy

## Next Steps

1. Run example analysis
2. Review output files
3. Explore individual modules
4. Customize for your case type
5. Integrate into workflow

## Support

For help:
1. Check README.md for detailed documentation
2. Review example-outputs.md for examples
3. Test with simple cases first
4. Verify API credentials

## Remember

- **For attorneys only**
- **Not legal advice**
- **Verify all citations**
- **Review required**
- **Professional judgment essential**

---

Ready to start? Run the example code above and explore the outputs!
