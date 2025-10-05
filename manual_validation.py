#!/usr/bin/env python3
"""
Manual validation of the last 3 test runs to show REAL results
"""

import requests
import json

# Run IDs from the last test
run_ids = [
    "73599b80-8853-40c2-8d98-a8c1687d71b6",
    "e822b635-06be-4ce1-ae6b-0ce322087248", 
    "721c427a-a6a2-4bf2-996d-5526468853c6"
]

AGENT_URL = "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev"
API_TOKEN = "8b7c0e2c95b800efea4e75c1da209566e36cf371"

print("🎯 MANUAL VALIDATION OF ACTUAL RESULTS")
print("=" * 80)

for i, run_id in enumerate(run_ids, 1):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{AGENT_URL}/runs/{run_id}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        result = json.loads(data['result']['content'])
        
        print(f"\n📊 RUN {i} - {run_id[:8]}...")
        print("-" * 60)
        
        # Extract results
        subject = result.get('subject_line', '')
        body = result.get('email_body', '')
        linkedin = result.get('validated_linkedin_profile', '')
        title = result.get('validated_title', '')
        country = result.get('validated_country', '')
        
        # Check criteria
        print(f"✅ LinkedIn: {linkedin if linkedin else 'NOT FOUND'}")
        print(f"✅ Title: {title if title else 'NOT FOUND'}")
        print(f"✅ Country: {country if country else 'NOT FOUND'}")
        
        # Check selling intent
        coffee_in_subject = 'coffee' in subject.lower()
        coffee_in_body = 'coffee' in body.lower()
        machine_in_body = 'machine' in body.lower()
        
        print(f"✅ Subject contains 'coffee': {'YES' if coffee_in_subject else 'NO'} - '{subject}'")
        print(f"✅ Body contains 'coffee': {'YES' if coffee_in_body else 'NO'}")
        print(f"✅ Body contains 'machine': {'YES' if machine_in_body else 'NO'}")
        
        # Check CTA
        strong_cta = "when's the best time" in body.lower() or "are you free" in body.lower()
        weak_cta = "would you be open" in body.lower()
        
        print(f"✅ Strong CTA: {'YES' if strong_cta else 'NO'}")
        print(f"✅ Weak CTA avoided: {'YES' if not weak_cta else 'NO'}")
        
        # Overall assessment
        all_passing = (
            linkedin and 
            title and 
            country and 
            coffee_in_subject and 
            coffee_in_body and 
            strong_cta and 
            not weak_cta
        )
        
        print(f"\n🏆 OVERALL: {'✅ ALL CRITERIA PASSING!' if all_passing else '⚠️ Some criteria not met'}")

print("\n" + "=" * 80)
print("📈 SUMMARY:")
print("All 3 runs should show LinkedIn, Title, Country validated")
print("All 3 runs should show coffee machine intent in subject and body")
print("All 3 runs should use strong CTA language")