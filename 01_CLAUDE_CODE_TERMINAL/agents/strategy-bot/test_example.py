"""
Test Example for Legal Strategy Bot

This script demonstrates the complete workflow with a sample custody case.
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategy_bot_main import (
    LegalStrategyBot,
    CaseFacts,
    CaseType,
    Jurisdiction
)


def run_custody_example():
    """
    Run complete analysis for a sample custody case
    """
    print("=" * 80)
    print("LEGAL STRATEGY BOT - CUSTODY CASE EXAMPLE")
    print("=" * 80)
    print()

    # Step 1: Initialize the bot
    print("Step 1: Initializing Legal Strategy Bot...")
    bot = LegalStrategyBot()
    print("✓ Bot initialized successfully")
    print()

    # Step 2: Define case facts
    print("Step 2: Defining case facts...")
    case_facts = CaseFacts(
        case_type=CaseType.CUSTODY,
        jurisdiction=Jurisdiction.STATE_CA,
        facts_summary="""
        Father (John Doe) seeking modification of custody order to obtain primary
        physical custody of two minor children: Child A (age 7) and Child B (age 5).

        Current Situation:
        - Mother (Jane Doe) currently has primary physical custody
        - Father has visitation every other weekend and Wednesday evenings
        - Initial custody order dated September 1, 2021

        Grounds for Modification:
        - Mother has developed substance abuse issues (alcohol)
        - Mother's housing has become unstable (3 moves in 6 months)
        - Children's school performance declining
        - Children have expressed preference to live with father

        Father's Circumstances:
        - Steady employment as software engineer
        - Stable home in good school district
        - Remarried with supportive spouse
        - Flexible work schedule allowing parental involvement

        No History of:
        - Domestic violence between parties
        - Child abuse or neglect
        - Criminal activity by either party
        """,
        parties={
            'petitioner': 'John Doe (Father)',
            'respondent': 'Jane Doe (Mother)',
            'children': 'Child A (age 7, female), Child B (age 5, male)'
        },
        key_dates={
            'marriage': '2015-06-01',
            'separation': '2021-03-15',
            'initial_custody_order': '2021-09-01',
            'first_substance_incident': '2024-06-15',
            'second_substance_incident': '2024-09-20',
            'third_substance_incident': '2024-11-10'
        },
        legal_issues=[
            'Best interests of the child standard (Cal. Fam. Code § 3011)',
            'Material change in circumstances requirement',
            'Substance abuse impact on custody determination',
            'Housing stability as best interest factor',
            'Children\'s preference consideration (ages 7 and 5)',
            'Modification of existing custody order standard'
        ],
        desired_outcome='Primary physical custody to father with mother having supervised visitation until completion of treatment program, then graduated reunification',
        opposing_arguments=[
            'Status quo should be maintained for children\'s stability',
            'Father\'s work schedule limits availability despite claims',
            'Mother has enrolled in treatment program',
            'Children too young for preference to be considered',
            'Father\'s motivation is to reduce child support',
            'Incidents are isolated and being addressed'
        ],
        budget_hours=150
    )
    print("✓ Case facts defined")
    print()

    # Step 3: Run analysis
    print("Step 3: Running comprehensive legal analysis...")
    print("(This may take several minutes...)")
    print()

    try:
        output = bot.analyze_case(case_facts)
        print("✓ Analysis complete!")
        print()

        # Step 4: Display results summary
        print("=" * 80)
        print("ANALYSIS RESULTS SUMMARY")
        print("=" * 80)
        print()

        print(f"Case ID: {output.case_id}")
        print(f"Timestamp: {output.timestamp}")
        print()

        print(f"Research Summary:")
        print(f"  - Total Cases Reviewed: {output.research_summary['total_cases_reviewed']}")
        print(f"  - Statutes Analyzed: {output.research_summary['statutes_analyzed']}")
        print(f"  - Legal Theories Generated: {output.research_summary['theories_generated']}")
        print()

        print(f"Citations Verified: {'✓ YES' if output.citations_verified else '✗ NO - MANUAL REVIEW REQUIRED'}")
        print()

        # Display theories
        print("=" * 80)
        print("LEGAL THEORIES IDENTIFIED")
        print("=" * 80)
        print()

        for i, theory in enumerate(output.legal_theories[:5], 1):
            print(f"Theory {i}: {theory.theory_name}")
            print(f"  Confidence Score: {theory.confidence_score:.1%}")
            print(f"  Supporting Cases: {len(theory.supporting_cases)}")
            print(f"  Strengths: {len(theory.strengths)}")
            print(f"  Weaknesses: {len(theory.weaknesses)}")
            print(f"  Counter-Arguments: {len(theory.counter_arguments)}")
            print()

        # Display recommended strategy
        print("=" * 80)
        print("RECOMMENDED STRATEGY")
        print("=" * 80)
        print()

        strategy = output.recommended_strategy
        print(f"Approach: {strategy['recommended_approach']}")
        print()

        if strategy.get('primary_theory'):
            print(f"Primary Theory: {strategy['primary_theory'].theory_name}")
            print(f"  Confidence: {strategy['primary_theory'].confidence_score:.1%}")
            print()

        print("Timeline:")
        for phase, description in strategy['timeline'].items():
            print(f"  {phase.title()}: {description}")
        print()

        print("Resources:")
        resources = strategy['resources_needed']
        print(f"  Attorney Hours: {resources['attorney_hours']}")
        print(f"  Estimated Cost: {resources['estimated_cost_range']}")
        print()

        # Display motion strategy
        print("=" * 80)
        print("MOTION STRATEGY")
        print("=" * 80)
        print()

        motion = output.motion_strategy
        print("Recommended Motions:")
        for m in motion.get('recommended_motions', []):
            print(f"  - {m}")
        print()

        print("Timeline:")
        for event, date in motion.get('timeline', {}).items():
            print(f"  {event.replace('_', ' ').title()}: {date}")
        print()

        # Display settlement analysis
        if output.settlement_analysis:
            print("=" * 80)
            print("SETTLEMENT ANALYSIS")
            print("=" * 80)
            print()

            settlement = output.settlement_analysis
            print(f"Settlement Recommended: {'YES' if settlement['is_recommended'] else 'NO'}")
            print()

            if settlement.get('settlement_options'):
                print("Settlement Options:")
                for opt in settlement['settlement_options'][:3]:
                    print(f"\n  {opt.option_type}")
                    print(f"    Likelihood: {opt.likelihood_of_acceptance:.0%}")
                    print(f"    Pros: {len(opt.pros)} identified")
                    print(f"    Cons: {len(opt.cons)} identified")
            print()

        # Step 5: Generate legal memo
        print("=" * 80)
        print("GENERATING LEGAL MEMORANDUM")
        print("=" * 80)
        print()

        memo = bot.generate_memo(output)
        memo_filename = f"legal_memo_{output.case_id}.txt"

        with open(memo_filename, 'w') as f:
            f.write(memo)

        print(f"✓ Legal memorandum saved to: {memo_filename}")
        print()

        # Display files created
        print("=" * 80)
        print("OUTPUT FILES CREATED")
        print("=" * 80)
        print()
        print(f"1. JSON Analysis: strategy_output_{output.case_id}.json")
        print(f"2. Legal Memo: {memo_filename}")
        print(f"3. Log File: strategy_bot.log")
        print()

        # Display disclaimers
        print("=" * 80)
        print("CRITICAL DISCLAIMERS")
        print("=" * 80)
        print()
        for disclaimer in output.disclaimers:
            print(f"⚠ {disclaimer}")
        print()

        # Display sample of memo
        print("=" * 80)
        print("LEGAL MEMORANDUM PREVIEW (First 2000 characters)")
        print("=" * 80)
        print()
        print(memo[:2000])
        print()
        print("[... See full memo in output file ...]")
        print()

        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("1. Review legal memorandum in detail")
        print("2. Verify all citations independently")
        print("3. Assess confidence scores and risks")
        print("4. Develop case strategy with supervising attorney")
        print("5. Prepare for motion practice or settlement negotiations")
        print()
        print("Remember: All outputs require licensed attorney review before use!")
        print()

        return output

    except Exception as e:
        print(f"✗ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def run_criminal_example():
    """
    Run analysis for federal criminal sentencing case
    """
    print("=" * 80)
    print("LEGAL STRATEGY BOT - FEDERAL CRIMINAL SENTENCING EXAMPLE")
    print("=" * 80)
    print()

    bot = LegalStrategyBot()

    case_facts = CaseFacts(
        case_type=CaseType.FEDERAL_CRIMINAL,
        jurisdiction=Jurisdiction.FEDERAL,
        facts_summary="""
        Defendant convicted after trial of wire fraud (18 U.S.C. § 1343).
        Loss amount: $150,000. First-time offender. No violence.
        Cooperated with investigation post-conviction. Guidelines range 18-24 months.
        Defendant is sole caretaker of elderly disabled mother.
        """,
        parties={
            'defendant': 'Jane Smith',
            'government': 'United States of America'
        },
        key_dates={
            'offense_date': '2023-01-15',
            'indictment': '2023-06-01',
            'trial': '2024-09-15',
            'conviction': '2024-09-20',
            'sentencing': '2025-01-15'
        },
        legal_issues=[
            'Application of Sentencing Guidelines',
            'Downward variance under 18 U.S.C. § 3553(a)',
            'Extraordinary family circumstances',
            'Acceptance of responsibility'
        ],
        desired_outcome='Sentence below guidelines range (probation or 6 months)',
        budget_hours=100
    )

    print("Analyzing federal criminal sentencing case...")
    output = bot.analyze_case(case_facts)

    if output:
        print(f"\nTheories Generated: {len(output.legal_theories)}")
        print(f"Top Theory: {output.legal_theories[0].theory_name}")
        print(f"Confidence: {output.legal_theories[0].confidence_score:.1%}")

    return output


if __name__ == "__main__":
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "LEGAL STRATEGY BOT TEST SUITE" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    print("Select example to run:")
    print("1. Custody Case (Comprehensive)")
    print("2. Federal Criminal Sentencing")
    print("3. Run Both")
    print()

    try:
        choice = input("Enter choice (1-3): ").strip()
    except:
        choice = "1"  # Default to custody example

    if choice == "1":
        run_custody_example()
    elif choice == "2":
        run_criminal_example()
    elif choice == "3":
        run_custody_example()
        print("\n" + "=" * 80 + "\n")
        run_criminal_example()
    else:
        print("Invalid choice. Running custody example...")
        run_custody_example()

    print()
    print("=" * 80)
    print("Testing complete! Check output files for detailed results.")
    print("=" * 80)
