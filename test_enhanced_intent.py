#!/usr/bin/env python3
"""
Test the enhanced selling intent enforcement system
"""

import sys
import os
sys.path.append('src')

from sales_personalized_email.email_quality_validator import EmailQualityValidator

def test_enhanced_intent_enforcement():
    """Test enhanced selling intent enforcement"""
    
    validator = EmailQualityValidator()
    print("🎯 TESTING ENHANCED SELLING INTENT ENFORCEMENT")
    print("=" * 60)
    
    # Test inputs
    sample_research = {
        'linkedin_confidence': 95,
        'achievements': ['Partner promotion'],
        'company_achievements': ['Industry leader']
    }
    
    sample_inputs_coffee = {
        'first_name': 'Milan',
        'company': 'Deloitte', 
        'title': 'Partner',
        'selling_intent': 'coffee machine data analytics and reporting'
    }
    
    # Test Case 1: GOOD Coffee Machine Email (should score high)
    print("\n📧 TEST 1: GOOD Coffee Machine Focus")
    print("-" * 50)
    
    good_coffee_email = """Subject: Coffee Machine Analytics - How Home Credit Cut Reporting Time 70%

Hi Milan,

Congratulations on your Partner role at Deloitte! Your supply chain expertise is impressive.

We recently helped Home Credit optimize their coffee machine operations data, achieving 70% reduction in manual reporting across their office facilities. Our platform automated their coffee consumption analytics and predictive maintenance scheduling.

Given Deloitte's focus on operational efficiency, I believe we could help you implement similar coffee machine analytics and reporting solutions for your facilities management.

Would you be open to a brief 15-minute call to explore coffee machine data optimization?

Best regards,"""

    score1 = validator.validate_email(good_coffee_email, sample_research, sample_inputs_coffee)
    
    # Test Case 2: BAD Generic Email (should score much lower now)
    print("\n📧 TEST 2: BAD Generic Data Platform (Should Score MUCH Lower)")
    print("-" * 50)
    
    bad_generic_email = """Subject: Data Platform Solutions for Deloitte

Hi Milan,

Congratulations on your Partner role at Deloitte! Your leadership is impressive.

We recently helped Home Credit achieve 70% reduction in FP&A reporting time using our data platform. Our solution consolidated their data sources and automated reporting.

Given your role at Deloitte, I believe we could help you achieve similar results with data transformation and analytics.

Would you be open to a brief 15-minute call to explore our data platform?

Best regards,"""

    score2 = validator.validate_email(bad_generic_email, sample_research, sample_inputs_coffee)
    
    # Test Case 3: No Intent (should not penalize)
    print("\n📧 TEST 3: No Selling Intent Specified (Should Not Penalize)")
    print("-" * 50)
    
    sample_inputs_no_intent = {
        'first_name': 'Milan',
        'company': 'Deloitte', 
        'title': 'Partner',
        'selling_intent': ''  # No intent
    }
    
    score3 = validator.validate_email(bad_generic_email, sample_research, sample_inputs_no_intent)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 ENHANCED SELLING INTENT RESULTS")
    print("=" * 60)
    
    print(f"✅ GOOD Coffee Email:")
    print(f"   Total: {score1.total_score}/100")
    print(f"   Structure: {score1.structure_score}/35")
    print(f"   Personalization: {score1.personalization_score}/25")
    print(f"   Message: {score1.message_score}/25")
    print(f"   🎯 SELLING INTENT: {score1.intent_score}/15")
    print(f"   Intent Details: {score1.details['selling_intent']['details']}")
    
    print(f"\n❌ BAD Generic Email (with coffee intent):")
    print(f"   Total: {score2.total_score}/100")
    print(f"   Structure: {score2.structure_score}/35")
    print(f"   Personalization: {score2.personalization_score}/25") 
    print(f"   Message: {score2.message_score}/25")
    print(f"   🎯 SELLING INTENT: {score2.intent_score}/15")
    print(f"   Intent Details: {score2.details['selling_intent']['details']}")
    
    print(f"\n✅ Generic Email (NO intent specified):")
    print(f"   Total: {score3.total_score}/100")
    print(f"   🎯 SELLING INTENT: {score3.intent_score}/15 (full points - no intent required)")
    
    # Calculate the difference
    score_difference = score1.total_score - score2.total_score
    intent_difference = score1.intent_score - score2.intent_score
    
    print(f"\n🚀 IMPROVEMENT ANALYSIS:")
    print(f"   Total Score Difference: {score_difference} points")
    print(f"   Intent Score Difference: {intent_difference} points")
    
    if score_difference >= 10:
        print(f"   ✅ EXCELLENT: {score_difference} point gap properly penalizes generic messaging!")
    elif score_difference >= 5:
        print(f"   ⚠️  GOOD: {score_difference} point gap, but could be stronger")
    else:
        print(f"   ❌ INSUFFICIENT: Only {score_difference} point gap - still too close")
        
    # Test acceptance thresholds
    print(f"\n📋 ACCEPTANCE ANALYSIS (85+ threshold):")
    print(f"   Good Coffee Email: {'✅ ACCEPT' if score1.total_score >= 85 else '❌ REJECT'} ({score1.total_score}/100)")
    print(f"   Bad Generic Email: {'✅ ACCEPT' if score2.total_score >= 85 else '❌ REJECT'} ({score2.total_score}/100)")
    print(f"   No Intent Email: {'✅ ACCEPT' if score3.total_score >= 85 else '❌ REJECT'} ({score3.total_score}/100)")


if __name__ == "__main__":
    test_enhanced_intent_enforcement()