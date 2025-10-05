#!/usr/bin/env python3
"""
Test how well the system handles specific selling intents
"""

import sys
import os
sys.path.append('src')

from sales_personalized_email.email_quality_validator import EmailQualityValidator

def test_selling_intent_scenarios():
    """Test various selling intent enforcement scenarios"""
    
    validator = EmailQualityValidator()
    print("🎯 TESTING SELLING INTENT ENFORCEMENT")
    print("=" * 60)
    
    # Test Case 1: Coffee Machine Intent - GOOD (specific focus)
    print("\n📧 TEST 1: Coffee Machine Intent - GOOD Implementation")
    print("-" * 50)
    
    good_coffee_email = """Subject: Coffee Machine Analytics - How Home Credit Cut Reporting Time 70%

Hi Milan,

Congratulations on your Partner role at Deloitte! Your supply chain expertise is impressive.

We recently helped Home Credit optimize their coffee machine operations data, achieving 70% reduction in manual reporting across their office facilities. Our platform automated their coffee consumption analytics and predictive maintenance scheduling.

Given Deloitte's focus on operational efficiency, I believe we could help you implement similar coffee machine analytics and reporting solutions for your facilities management.

Would you be open to a brief 15-minute call to explore coffee machine data optimization?

Best regards,"""

    sample_inputs_coffee = {
        'first_name': 'Milan',
        'company': 'Deloitte', 
        'title': 'Partner',
        'selling_intent': 'coffee machine data analytics and reporting'
    }
    
    # Test Case 2: Coffee Machine Intent - BAD (generic data platform)
    print("\n📧 TEST 2: Coffee Machine Intent - BAD Implementation")
    print("-" * 50)
    
    bad_coffee_email = """Subject: Data Platform Solutions for Deloitte

Hi Milan,

Congratulations on your Partner role at Deloitte! Your leadership is impressive.

We recently helped Home Credit achieve 70% reduction in FP&A reporting time using our data platform. Our solution consolidated their data sources and automated reporting.

Given your role at Deloitte, I believe we could help you achieve similar results with data transformation and analytics.

Would you be open to a brief 15-minute call to explore our data platform?

Best regards,"""

    sample_research = {
        'linkedin_confidence': 95,
        'achievements': ['Partner promotion'],
        'company_achievements': ['Industry leader']
    }
    
    # Test with coffee machine intent
    score1 = validator.validate_email(good_coffee_email, sample_research, sample_inputs_coffee)
    score2 = validator.validate_email(bad_coffee_email, sample_research, sample_inputs_coffee)
    
    print(f"✅ GOOD Coffee Email Score: {score1.total_score}/100")
    print(f"❌ BAD Coffee Email Score: {score2.total_score}/100")
    
    # Check if our validator catches selling intent issues
    coffee_intent_score1 = check_selling_intent_compliance(good_coffee_email, sample_inputs_coffee)
    coffee_intent_score2 = check_selling_intent_compliance(bad_coffee_email, sample_inputs_coffee)
    
    print(f"☕ GOOD Email - Intent Compliance: {coffee_intent_score1}/10")
    print(f"☕ BAD Email - Intent Compliance: {coffee_intent_score2}/10")
    
    # Test Case 3: Different Intent - CRM Analytics
    print("\n📧 TEST 3: CRM Analytics Intent")
    print("-" * 50)
    
    crm_email = """Subject: CRM Analytics Transformation - How BRIX Reduced Manual Processing 80%

Hi Milan,

Congratulations on your Partner role at Deloitte! Your automotive expertise is remarkable.

We recently helped BRIX optimize their CRM analytics pipeline, achieving 80% reduction in manual customer data processing. Our platform automated lead scoring and customer segmentation workflows.

Given Deloitte's consulting focus, I believe we could help you implement advanced CRM analytics and automated reporting for your client management processes.

Would you be open to a brief 15-minute call to explore CRM data optimization solutions?

Best regards,"""

    sample_inputs_crm = {
        'first_name': 'Milan',
        'company': 'Deloitte', 
        'title': 'Partner',
        'selling_intent': 'CRM analytics and customer data management'
    }
    
    score3 = validator.validate_email(crm_email, sample_research, sample_inputs_crm)
    crm_intent_score = check_selling_intent_compliance(crm_email, sample_inputs_crm)
    
    print(f"📊 CRM Email Score: {score3.total_score}/100")
    print(f"🎯 CRM Intent Compliance: {crm_intent_score}/10")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 SELLING INTENT ENFORCEMENT ANALYSIS")
    print("=" * 60)
    print(f"☕ Coffee Machine (GOOD): {coffee_intent_score1}/10 intent compliance")
    print(f"☕ Coffee Machine (BAD):  {coffee_intent_score2}/10 intent compliance") 
    print(f"📊 CRM Analytics:         {crm_intent_score}/10 intent compliance")
    print()
    print("🚨 IDENTIFIED ISSUES:")
    if coffee_intent_score2 > 3:
        print("❌ Current validator doesn't strongly penalize generic messaging when specific intent provided")
    if coffee_intent_score1 < 8:
        print("❌ Even 'good' implementation could be more intent-focused")
    print()
    print("💡 RECOMMENDATIONS:")
    print("1. Strengthen selling intent validation in quality scorer")
    print("2. Add specific intent keywords checking")
    print("3. Penalize generic data platform messaging when specific intent given")
    print("4. Require use case examples relevant to the specific intent")


def check_selling_intent_compliance(email: str, inputs: dict) -> int:
    """
    Custom function to check selling intent compliance (0-10 score)
    This shows what we SHOULD be checking for
    """
    
    selling_intent = inputs.get('selling_intent', '').lower()
    email_lower = email.lower()
    score = 0
    
    if not selling_intent:
        return 5  # No intent specified, generic is okay
    
    # Extract key intent words
    intent_keywords = selling_intent.split()
    
    # Check if ALL intent keywords appear in email
    keywords_found = sum(1 for keyword in intent_keywords if keyword in email_lower)
    keyword_coverage = keywords_found / len(intent_keywords) if intent_keywords else 0
    
    if keyword_coverage >= 0.8:  # 80% of keywords present
        score += 4
    elif keyword_coverage >= 0.5:  # 50% of keywords present
        score += 2
    
    # Check for specific use case focus (not generic)
    if 'coffee machine' in selling_intent:
        if 'coffee' in email_lower and ('machine' in email_lower or 'facilities' in email_lower):
            score += 3
        if 'consumption analytics' in email_lower or 'predictive maintenance' in email_lower:
            score += 2
        # Penalize generic data platform messaging
        if 'data platform' in email_lower and 'coffee' not in email_lower:
            score -= 3
            
    elif 'crm' in selling_intent:
        if 'crm' in email_lower:
            score += 3
        if 'customer' in email_lower and ('analytics' in email_lower or 'segmentation' in email_lower):
            score += 2
            
    # Check if CTA mentions the intent
    if any(keyword in email_lower for keyword in intent_keywords):
        if 'call to explore' in email_lower:
            score += 1
            
    return max(0, min(10, score))


if __name__ == "__main__":
    test_selling_intent_scenarios()