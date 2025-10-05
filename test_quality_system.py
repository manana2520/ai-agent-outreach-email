#!/usr/bin/env python3
"""
Test the complete quality validation system with sample emails
"""

import sys
import os
sys.path.append('src')

from sales_personalized_email.email_quality_validator import EmailQualityValidator, validate_and_improve_email

def test_quality_scenarios():
    """Test various email quality scenarios"""
    
    validator = EmailQualityValidator()
    print("🧪 TESTING EMAIL QUALITY VALIDATION SYSTEM")
    print("=" * 60)
    
    # Test Case 1: High-quality email (should score 85+)
    print("\n📧 TEST 1: High-Quality Email")
    print("-" * 40)
    
    high_quality_email = """Subject: Congratulations on Partner Promotion - How P3 Cut Data Costs 50%

Hi Milan,

Congratulations on your promotion to Partner at Deloitte! Your leadership in automotive and supply chain transformation is impressive.

We recently helped P3 Logistic Parks unify data across 8 countries using our data platform. This eliminated operational silos and reduced reporting time by 70%.

Given your role at Deloitte and expertise in supply chain optimization, I believe we could help you achieve similar results for your coffee machine analytics initiatives.

Would you be open to a brief 15-minute call to explore how this might apply to your situation?

Best regards,"""

    sample_research = {
        'linkedin_confidence': 95,
        'achievements': ['Partner promotion', 'Automotive leader'],
        'company_achievements': ['Deloitte consulting excellence', 'Industry leadership']
    }
    
    sample_inputs = {
        'first_name': 'Milan',
        'company': 'Deloitte', 
        'title': 'Partner',
        'selling_intent': 'coffee machine data analytics and reporting'
    }
    
    score1 = validator.validate_email(high_quality_email, sample_research, sample_inputs)
    should_regen1, reason1 = validator.should_regenerate(score1)
    
    print(f"📊 Score: {score1.total_score}/100")
    print(f"   Structure: {score1.structure_score}/40")
    print(f"   Personalization: {score1.personalization_score}/30")
    print(f"   Message: {score1.message_score}/30")
    print(f"🔄 Should Regenerate: {should_regen1} ({reason1})")
    
    # Test Case 2: Medium-quality email (should score 70-84)
    print("\n📧 TEST 2: Medium-Quality Email")
    print("-" * 40)
    
    medium_quality_email = """Subject: Data Solutions for Deloitte

Hi milan,

I noticed Deloitte is doing great work. We help companies with data.

We worked with some clients and got good results. Our platform helps with data stuff.

I think we can help you too with your business needs.

Want to chat sometime?

Thanks,"""

    sample_research_med = {
        'linkedin_confidence': 60,
        'achievements': ['Industry work'],
        'company_achievements': ['Good reputation']
    }
    
    score2 = validator.validate_email(medium_quality_email, sample_research_med, sample_inputs)
    should_regen2, reason2 = validator.should_regenerate(score2)
    
    print(f"📊 Score: {score2.total_score}/100") 
    print(f"   Structure: {score2.structure_score}/40")
    print(f"   Personalization: {score2.personalization_score}/30")
    print(f"   Message: {score2.message_score}/30")
    print(f"🔄 Should Regenerate: {should_regen2} ({reason2})")
    
    if should_regen2:
        suggestions = validator.get_improvement_suggestions(score2)
        print(f"💡 Suggestions: {suggestions}")
    
    # Test Case 3: Low-quality email (should score <70)
    print("\n📧 TEST 3: Low-Quality Email")
    print("-" * 40)
    
    low_quality_email = """hi there
    
we sell data tools
want to buy?
    
bye"""

    sample_research_low = {
        'linkedin_confidence': 20,
        'achievements': [],
        'company_achievements': []
    }
    
    score3 = validator.validate_email(low_quality_email, sample_research_low, sample_inputs)
    should_regen3, reason3 = validator.should_regenerate(score3)
    
    print(f"📊 Score: {score3.total_score}/100")
    print(f"   Structure: {score3.structure_score}/40")
    print(f"   Personalization: {score3.personalization_score}/30") 
    print(f"   Message: {score3.message_score}/30")
    print(f"🔄 Should Regenerate: {should_regen3} ({reason3})")
    
    if should_regen3:
        suggestions = validator.get_improvement_suggestions(score3)
        print(f"💡 Suggestions: {suggestions}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 QUALITY VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ High-Quality Email: {score1.total_score}/100 - {'ACCEPT' if not should_regen1 else 'REGENERATE'}")
    print(f"⚠️  Medium-Quality Email: {score2.total_score}/100 - {'ACCEPT' if not should_regen2 else 'OPTIMIZE'}")
    print(f"❌ Low-Quality Email: {score3.total_score}/100 - {'ACCEPT' if not should_regen3 else 'REGENERATE'}")
    
    # Test the auto-improvement function
    print(f"\n🔄 TESTING AUTO-IMPROVEMENT LOOP")
    print("-" * 40)
    
    final_email, final_score, attempts = validate_and_improve_email(
        medium_quality_email, sample_research_med, sample_inputs, max_attempts=2
    )
    
    print(f"📈 Final Score: {final_score.total_score}/100 after {attempts} attempts")
    print(f"✅ Auto-improvement system {'PASSED' if final_score.total_score >= 70 else 'NEEDS HUMAN REVIEW'}")


if __name__ == "__main__":
    test_quality_scenarios()