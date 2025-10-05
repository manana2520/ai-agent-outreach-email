#!/usr/bin/env python3
"""
Analyze the one successful run in detail
"""

import sys
import json
sys.path.append('src')
from sales_personalized_email.email_quality_validator import EmailQualityValidator

def analyze_successful_run():
    """Analyze the successful run from the test"""
    
    print("🔍 DETAILED ANALYSIS OF SUCCESSFUL RUN")
    print("=" * 70)
    
    # The actual result from the successful run
    result_data = {
        "subject_line": "Unlock Coffee Insights with Keboola",
        "email_body": "Milan, your leadership and innovative strategies at Deloitte are commendable.\n\nWe've helped companies like Apify achieve a 3.5 engineering days savings monthly through advanced automation and insights.\n\nKeboola can help you enhance facilities management by leveraging predictive analytics for your coffee operations, resulting in improved maintenance and consumption efficiency.\n\nWhen's the best time for a 15-minute call to discuss these benefits?\nBest,",
        "follow_up_notes": "Key talking points: Milan's leadership at Deloitte, Apify's success with Keboola, benefits of predictive analytics for coffee operations.",
        "validated_title": None,
        "validated_linkedin_profile": None,
        "validated_country": None
    }
    
    full_email = f"Subject: {result_data['subject_line']}\n\n{result_data['email_body']}"
    
    print("📧 EMAIL CONTENT:")
    print(f"Subject: {result_data['subject_line']}")
    print(f"Body:\n{result_data['email_body']}")
    print(f"Follow-up Notes: {result_data['follow_up_notes']}")
    
    print(f"\n🔍 VALIDATION RESULTS:")
    print(f"LinkedIn Profile: {result_data['validated_linkedin_profile'] or 'NOT FOUND ❌'}")
    print(f"Title: {result_data['validated_title'] or 'NOT FOUND ❌'}")
    print(f"Country: {result_data['validated_country'] or 'NOT FOUND ❌'}")
    
    # Quality analysis
    validator = EmailQualityValidator()
    
    research_data = {
        'linkedin_confidence': 0,  # No LinkedIn found
        'achievements': [],
        'company_achievements': ['Deloitte leadership']
    }
    
    inputs = {
        'first_name': 'Milan',
        'company': 'Deloitte',
        'selling_intent': 'coffee machine'
    }
    
    quality_score = validator.validate_email(full_email, research_data, inputs)
    
    print(f"\n📊 QUALITY SCORE BREAKDOWN:")
    print(f"Total Score: {quality_score.total_score}/100")
    print(f"Structure: {quality_score.structure_score}/35")
    print(f"Personalization: {quality_score.personalization_score}/25")
    print(f"Message: {quality_score.message_score}/25")
    print(f"Selling Intent: {quality_score.intent_score}/15")
    
    print(f"\n🎯 DETAILED EVALUATION:")
    
    # LinkedIn validation
    print(f"\n❌ LINKEDIN VALIDATION FAILURE:")
    print(f"   Expected: https://www.linkedin.com/in/milan-kulh%C3%A1nek/")
    print(f"   Actual: None found")
    print(f"   Issue: Agent failed to validate obvious exact match")
    
    # Title validation  
    print(f"\n❌ TITLE EXTRACTION FAILURE:")
    print(f"   Expected: Partner at Deloitte")
    print(f"   Actual: None found")
    print(f"   Issue: Should have extracted from LinkedIn")
    
    # Country detection
    print(f"\n❌ COUNTRY DETECTION FAILURE:")
    print(f"   Expected: Czech Republic (from .cz domain)")
    print(f"   Actual: None found")
    print(f"   Issue: Should have inferred from LinkedIn domain")
    
    # Selling intent compliance
    print(f"\n✅ SELLING INTENT COMPLIANCE - IMPROVED:")
    coffee_mentioned = "coffee" in full_email.lower()
    facilities_mentioned = "facilities" in full_email.lower()
    predictive_mentioned = "predictive" in full_email.lower()
    maintenance_mentioned = "maintenance" in full_email.lower()
    
    print(f"   Coffee mentioned: {'✅' if coffee_mentioned else '❌'}")
    print(f"   Facilities mentioned: {'✅' if facilities_mentioned else '❌'}")
    print(f"   Predictive analytics mentioned: {'✅' if predictive_mentioned else '❌'}")
    print(f"   Maintenance mentioned: {'✅' if maintenance_mentioned else '❌'}")
    print(f"   Subject line relevant: {'✅' if 'coffee' in result_data['subject_line'].lower() else '❌'}")
    
    # CTA analysis
    print(f"\n✅ CTA ANALYSIS - IMPROVED:")
    cta_text = result_data['email_body'].lower()
    strong_cta = "when's the best time" in cta_text
    weak_cta = any(phrase in cta_text for phrase in ["would you be open", "are you interested"])
    
    print(f"   Strong assumptive CTA: {'✅' if strong_cta else '❌'}")
    print(f"   Weak permission-seeking CTA: {'❌' if weak_cta else '✅ (avoided)'}")
    print(f"   CTA Text: 'When's the best time for a 15-minute call to discuss these benefits?'")
    
    # Issues found
    print(f"\n🚨 ISSUES IDENTIFIED:")
    issues = []
    
    if not result_data['validated_linkedin_profile']:
        issues.append("CRITICAL: LinkedIn validation completely failed")
    if not result_data['validated_title']:
        issues.append("CRITICAL: Title extraction failed")  
    if not result_data['validated_country']:
        issues.append("CRITICAL: Country detection failed")
    if quality_score.total_score < 85:
        issues.append(f"QUALITY: Overall score {quality_score.total_score}/100 below 85 threshold")
    
    # Check for wrong customer example
    if "apify" in full_email.lower():
        issues.append("MEDIUM: Uses Apify example instead of relevant coffee machine customer")
    
    for issue in issues:
        print(f"   ❌ {issue}")
    
    # Improvements noted
    print(f"\n✅ IMPROVEMENTS CONFIRMED:")
    improvements = []
    
    if coffee_mentioned:
        improvements.append("Selling intent enforcement working - mentions coffee")
    if facilities_mentioned:
        improvements.append("Uses relevant facilities management terminology")
    if strong_cta:
        improvements.append("Uses strong assumptive CTA instead of weak permission-seeking")
    if "sustainability" not in full_email.lower():
        improvements.append("No longer incorrectly mentions sustainability")
    if predictive_mentioned and maintenance_mentioned:
        improvements.append("Uses relevant coffee machine analytics terminology")
    
    for improvement in improvements:
        print(f"   ✅ {improvement}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   LinkedIn Validation: ❌ FAILING (0% success)")
    print(f"   Selling Intent Compliance: ✅ WORKING (focuses on coffee machine)")
    print(f"   CTA Improvement: ✅ WORKING (uses assumptive language)")
    print(f"   Overall Quality: ❌ BELOW THRESHOLD (20/100)")
    
    print(f"\n💡 NEXT STEPS NEEDED:")
    print(f"   1. Fix LinkedIn research agent - still not finding obvious matches")
    print(f"   2. Improve overall email quality scoring")
    print(f"   3. Use more relevant customer examples for coffee machine use cases")
    print(f"   4. Ensure validation fields are properly returned")

if __name__ == "__main__":
    analyze_successful_run()