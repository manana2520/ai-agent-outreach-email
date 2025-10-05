#!/usr/bin/env python3
"""
Run 10 iterations of the agent and evaluate each against quality criteria
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

sys.path.append('src')
from sales_personalized_email.email_quality_validator import EmailQualityValidator

# Test configuration
AGENT_URL = "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev"
API_TOKEN = "8b7c0e2c95b800efea4e75c1da209566e36cf371"
NUM_RUNS = 3  # Start with 3 to validate

# Expected results for validation
EXPECTED_LINKEDIN = "https://www.linkedin.com/in/milan-kulh%C3%A1nek"
EXPECTED_TITLE = "Partner"  # Should contain this
EXPECTED_COMPANY = "Deloitte"
EXPECTED_COUNTRY = "Czech Republic" 
SELLING_INTENT = "coffee machine"

def run_single_test(run_number):
    """Run a single test iteration"""
    print(f"\n🧪 RUN {run_number}/10 - Starting...")
    
    # Trigger agent
    payload = {
        "crew": "sales_personalized_email",
        "inputs": {
            "first_name": "Milan",
            "last_name": "Kulhanek",
            "title": "",
            "company": "Deloitte", 
            "phone": "",
            "country": "",
            "linkedin_profile": "",
            "selling_intent": "coffee machine"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Start run
        response = requests.post(f"{AGENT_URL}/kickoff", headers=headers, json=payload)
        if response.status_code not in [200, 202]:
            return {"error": f"Failed to start run: {response.status_code} - {response.text}"}
        
        run_data = response.json()
        run_id = run_data["run_id"]
        print(f"   Run ID: {run_id}")
        
        # Poll for completion
        max_wait = 300  # 5 minutes timeout
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(10)
            wait_time += 10
            
            status_response = requests.get(f"{AGENT_URL}/runs/{run_id}", headers=headers)
            if status_response.status_code != 200:
                return {"error": f"Failed to get status: {status_response.status_code}"}
            
            status_data = status_response.json()
            status = status_data["status"]
            
            print(f"   Status: {status} (waited {wait_time}s)")
            
            if status == "completed":
                result = status_data.get("result", {})
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "result": result,
                    "wait_time": wait_time
                }
            elif status == "failed":
                return {
                    "run_id": run_id, 
                    "status": "failed",
                    "error": status_data.get("error", "Unknown error"),
                    "wait_time": wait_time
                }
        
        return {"error": f"Timeout after {max_wait}s"}
        
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def evaluate_run_quality(run_data, run_number):
    """Evaluate a single run against quality criteria"""
    
    if "error" in run_data:
        return {
            "run": run_number,
            "success": False,
            "error": run_data["error"],
            "scores": {}
        }
    
    result = run_data.get("result", {})
    
    # Extract email components
    subject_line = result.get("subject_line", "")
    email_body = result.get("email_body", "")
    follow_up_notes = result.get("follow_up_notes", "")
    
    # Validated information
    linkedin_profile = result.get("linkedin_profile_validated", "")
    validated_title = result.get("validated_title", "")
    validated_country = result.get("validated_country", "")
    
    # Create full email for quality validation
    full_email = f"Subject: {subject_line}\n\n{email_body}"
    
    # Quality validation
    validator = EmailQualityValidator()
    
    # Simulate research data
    research_data = {
        'linkedin_confidence': 95 if linkedin_profile else 0,
        'achievements': ['Partner at Deloitte'] if 'Partner' in validated_title else [],
        'company_achievements': ['Deloitte consulting excellence']
    }
    
    inputs = {
        'first_name': 'Milan',
        'company': 'Deloitte',
        'selling_intent': 'coffee machine'
    }
    
    quality_score = validator.validate_email(full_email, research_data, inputs)
    
    # Evaluation criteria
    evaluation = {
        "run": run_number,
        "success": True,
        "run_id": run_data.get("run_id", ""),
        "wait_time": run_data.get("wait_time", 0),
        
        # Email content
        "subject_line": subject_line,
        "email_body": email_body,
        "email_length": len(email_body.split()),
        
        # Validation results  
        "linkedin_found": bool(linkedin_profile),
        "linkedin_correct": EXPECTED_LINKEDIN in linkedin_profile if linkedin_profile else False,
        "title_found": bool(validated_title),
        "title_correct": EXPECTED_TITLE in validated_title if validated_title else False,
        "country_found": bool(validated_country),
        "country_correct": EXPECTED_COUNTRY in validated_country if validated_country else False,
        
        # Content analysis
        "selling_intent_compliance": {
            "coffee_mentioned": "coffee" in full_email.lower(),
            "machine_mentioned": "machine" in full_email.lower(),
            "facilities_mentioned": any(word in full_email.lower() for word in ["facilities", "consumption", "maintenance"]),
            "sustainability_wrongly_mentioned": "sustainability" in full_email.lower(),
            "generic_data_platform": "data platform" in full_email.lower() and "coffee" not in full_email.lower()
        },
        
        # CTA analysis
        "cta_analysis": {
            "has_cta": any(phrase in email_body.lower() for phrase in ["call", "meeting", "discuss"]),
            "strong_cta": any(phrase in email_body.lower() for phrase in ["when's the best time", "are you free", "when can we"]),
            "weak_cta": any(phrase in email_body.lower() for phrase in ["would you be open", "are you interested"])
        },
        
        # Quality scores
        "quality_score": {
            "total": quality_score.total_score,
            "structure": quality_score.structure_score,
            "personalization": quality_score.personalization_score,
            "message": quality_score.message_score,
            "intent": quality_score.intent_score,
            "acceptable": quality_score.total_score >= 85
        }
    }
    
    return evaluation

def run_comprehensive_test():
    """Run all 10 tests and create summary"""
    
    print("🚀 STARTING 10-RUN COMPREHENSIVE AGENT TEST")
    print("=" * 70)
    print(f"Target: Milan Kulhanek, Deloitte, coffee machine use case")
    print(f"Expected LinkedIn: {EXPECTED_LINKEDIN}")
    print(f"Expected Title: Partner at Deloitte")
    print(f"Expected Country: Czech Republic")
    print("=" * 70)
    
    all_results = []
    successful_runs = 0
    
    # Run all tests
    for i in range(1, NUM_RUNS + 1):
        run_data = run_single_test(i)
        evaluation = evaluate_run_quality(run_data, i)
        all_results.append(evaluation)
        
        if evaluation["success"]:
            successful_runs += 1
            print(f"   ✅ Completed - Quality: {evaluation['quality_score']['total']}/100")
        else:
            print(f"   ❌ Failed - {evaluation.get('error', 'Unknown error')}")
    
    print(f"\n📊 SUMMARY: {successful_runs}/{NUM_RUNS} successful runs")
    
    # Generate summary table
    generate_summary_table(all_results)
    
    return all_results

def generate_summary_table(results):
    """Generate comprehensive summary table"""
    
    print(f"\n{'='*120}")
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print(f"{'='*120}")
    
    # Header
    print(f"{'Run':<3} {'Success':<7} {'Quality':<7} {'LinkedIn':<8} {'Title':<6} {'Country':<7} {'Coffee':<6} {'CTA':<8} {'Issues':<20}")
    print(f"{'-'*120}")
    
    # Results
    for result in results:
        if not result["success"]:
            print(f"{result['run']:<3} {'❌':<7} {'N/A':<7} {'❌':<8} {'❌':<6} {'❌':<7} {'❌':<6} {'❌':<8} {result.get('error', 'Failed')[:20]:<20}")
            continue
            
        quality = result["quality_score"]["total"]
        linkedin = "✅" if result["linkedin_correct"] else ("⚠️" if result["linkedin_found"] else "❌")
        title = "✅" if result["title_correct"] else ("⚠️" if result["title_found"] else "❌")
        country = "✅" if result["country_correct"] else ("⚠️" if result["country_found"] else "❌")
        coffee = "✅" if result["selling_intent_compliance"]["coffee_mentioned"] else "❌"
        cta = "STRONG" if result["cta_analysis"]["strong_cta"] else ("WEAK" if result["cta_analysis"]["weak_cta"] else "NONE")
        
        issues = []
        if result["selling_intent_compliance"]["sustainability_wrongly_mentioned"]:
            issues.append("SUSTAIN")
        if result["selling_intent_compliance"]["generic_data_platform"]:
            issues.append("GENERIC")
        if not result["selling_intent_compliance"]["coffee_mentioned"]:
            issues.append("NO-COFFEE")
        
        issues_str = ",".join(issues[:2])  # Limit to 2 issues for space
        
        print(f"{result['run']:<3} {'✅':<7} {quality:<7} {linkedin:<8} {title:<6} {country:<7} {coffee:<6} {cta:<8} {issues_str:<20}")
    
    # Statistics
    successful_results = [r for r in results if r["success"]]
    if not successful_results:
        print(f"\n❌ NO SUCCESSFUL RUNS - SYSTEM COMPLETELY BROKEN")
        return
    
    print(f"\n{'='*120}")
    print("📈 STATISTICS")
    print(f"{'='*120}")
    
    # Success rates
    success_rate = len(successful_results) / len(results) * 100
    linkedin_success = sum(1 for r in successful_results if r["linkedin_correct"]) / len(successful_results) * 100
    title_success = sum(1 for r in successful_results if r["title_correct"]) / len(successful_results) * 100
    country_success = sum(1 for r in successful_results if r["country_correct"]) / len(successful_results) * 100
    coffee_compliance = sum(1 for r in successful_results if r["selling_intent_compliance"]["coffee_mentioned"]) / len(successful_results) * 100
    strong_cta_rate = sum(1 for r in successful_results if r["cta_analysis"]["strong_cta"]) / len(successful_results) * 100
    
    avg_quality = sum(r["quality_score"]["total"] for r in successful_results) / len(successful_results)
    quality_acceptable = sum(1 for r in successful_results if r["quality_score"]["acceptable"]) / len(successful_results) * 100
    
    print(f"Overall Success Rate:        {success_rate:.1f}%")
    print(f"LinkedIn Validation:         {linkedin_success:.1f}%")
    print(f"Title Extraction:            {title_success:.1f}%")
    print(f"Country Detection:           {country_success:.1f}%")
    print(f"Selling Intent Compliance:   {coffee_compliance:.1f}%")
    print(f"Strong CTA Usage:           {strong_cta_rate:.1f}%")
    print(f"Average Quality Score:       {avg_quality:.1f}/100")
    print(f"Quality Acceptable (≥85):    {quality_acceptable:.1f}%")
    
    # Issue analysis
    sustainability_issues = sum(1 for r in successful_results if r["selling_intent_compliance"]["sustainability_wrongly_mentioned"])
    generic_issues = sum(1 for r in successful_results if r["selling_intent_compliance"]["generic_data_platform"])
    
    print(f"\n🚨 ISSUE FREQUENCY:")
    print(f"Sustainability instead of coffee: {sustainability_issues}/{len(successful_results)} runs")
    print(f"Generic data platform messaging: {generic_issues}/{len(successful_results)} runs")
    
    # Final assessment
    print(f"\n{'='*120}")
    print("🎯 FINAL ASSESSMENT")
    print(f"{'='*120}")
    
    if success_rate < 80:
        print("❌ SYSTEM RELIABILITY: POOR - Too many failed runs")
    elif linkedin_success < 80:
        print("❌ LINKEDIN VALIDATION: FAILING - Not consistently finding correct profile")
    elif coffee_compliance < 80:
        print("❌ SELLING INTENT: FAILING - Not consistently focusing on coffee machine")
    elif avg_quality < 85:
        print("⚠️  QUALITY: NEEDS IMPROVEMENT - Average quality below acceptable threshold")
    elif quality_acceptable < 80:
        print("⚠️  CONSISTENCY: NEEDS IMPROVEMENT - Too many low-quality emails")
    else:
        print("✅ SYSTEM: WORKING CORRECTLY - Meeting all quality requirements")
        
    print(f"{'='*120}")

if __name__ == "__main__":
    run_comprehensive_test()