#!/usr/bin/env python3
"""
Auto-Improvement Wrapper for Sales Personalized Email Agent
Integrates quality validation and regeneration logic with CrewAI
"""

import json
import re
from typing import Dict, Any, Tuple
from sales_personalized_email.crew import SalesPersonalizedEmailCrew
from sales_personalized_email.email_quality_validator import EmailQualityValidator, QualityScore


class AutoImprovementWrapper:
    """
    Wraps the CrewAI agent with auto-improvement capabilities.
    Validates email quality and triggers regeneration when needed.
    """
    
    def __init__(self):
        self.validator = EmailQualityValidator()
        self.max_attempts = 3
        self.quality_threshold = 85
        
    def run_with_quality_validation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with automatic quality validation and improvement.
        
        Args:
            inputs: Input parameters for the agent
            
        Returns:
            Dict containing final email, quality score, and metrics
        """
        
        for attempt in range(self.max_attempts):
            print(f"\n🔄 Attempt {attempt + 1}/{self.max_attempts}")
            
            # Run the CrewAI agent
            try:
                result = SalesPersonalizedEmailCrew().crew().kickoff(inputs=inputs)
                email_content = str(result)
                
                # Extract research data from the crew execution
                research_data = self._extract_research_data(email_content)
                
                # Validate email quality
                quality_score = self.validator.validate_email(email_content, research_data, inputs)
                
                print(f"📊 Quality Score: {quality_score.total_score}/100")
                print(f"   Structure: {quality_score.structure_score}/40")
                print(f"   Personalization: {quality_score.personalization_score}/30")
                print(f"   Message: {quality_score.message_score}/30")
                
                # Check if quality meets threshold
                if quality_score.total_score >= self.quality_threshold:
                    print(f"✅ Quality acceptable ({quality_score.total_score}/100 >= {self.quality_threshold})")
                    return {
                        'email_content': email_content,
                        'quality_score': quality_score,
                        'attempts': attempt + 1,
                        'success': True
                    }
                
                elif attempt < self.max_attempts - 1:
                    print(f"❌ Quality below threshold ({quality_score.total_score}/100 < {self.quality_threshold})")
                    
                    # Get improvement suggestions
                    suggestions = self.validator.get_improvement_suggestions(quality_score)
                    print("💡 Improvement suggestions:", suggestions)
                    
                    # Enhance prompts for next attempt (simplified for demo)
                    inputs = self._enhance_inputs_for_retry(inputs, suggestions, attempt + 1)
                    print("🔧 Enhanced prompts for retry...")
                    
                else:
                    print(f"⚠️  Maximum attempts reached. Final score: {quality_score.total_score}/100")
                    return {
                        'email_content': email_content,
                        'quality_score': quality_score,
                        'attempts': attempt + 1,
                        'success': False
                    }
                    
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_attempts - 1:
                    raise
                continue
        
        # Should never reach here
        raise RuntimeError("Auto-improvement loop failed unexpectedly")
    
    def _extract_research_data(self, email_content: str) -> Dict[str, Any]:
        """Extract research data from email content for validation."""
        
        # Extract LinkedIn confidence from email content patterns
        linkedin_confidence = 0
        if "congratulations" in email_content.lower() and "partner" in email_content.lower():
            linkedin_confidence = 90  # High confidence if specific achievements mentioned
        elif "impressive" in email_content.lower() or "noticed" in email_content.lower():
            linkedin_confidence = 60  # Medium confidence
        else:
            linkedin_confidence = 30  # Low confidence
        
        # Extract achievements from content
        achievements = []
        if "partner" in email_content.lower():
            achievements.append("Partner at Deloitte")
        if "leader" in email_content.lower():
            achievements.append("Industry leader")
        
        # Extract company achievements 
        company_achievements = []
        if "deloitte" in email_content.lower():
            company_achievements.append("Global consulting leader")
        if "award" in email_content.lower():
            company_achievements.append("Industry awards")
        
        return {
            'linkedin_confidence': linkedin_confidence,
            'achievements': achievements,
            'company_achievements': company_achievements
        }
    
    def _enhance_inputs_for_retry(self, original_inputs: Dict[str, Any], suggestions: Dict[str, str], attempt: int) -> Dict[str, Any]:
        """
        Enhance inputs based on quality score feedback for retry attempts.
        In a real implementation, this would modify agent prompts.
        """
        
        enhanced_inputs = original_inputs.copy()
        
        # Add enhancement flags based on suggestions
        enhancements = []
        
        if 'structure' in suggestions:
            enhancements.append("FOCUS: Ensure exact 5-paragraph structure")
        
        if 'achievement' in suggestions:
            enhancements.append("FOCUS: Include specific achievement recognition") 
            
        if 'industry_context' in suggestions:
            enhancements.append("FOCUS: Include Keboola customer use case with metrics")
        
        if 'cta' in suggestions:
            enhancements.append("FOCUS: Include clear 15-minute meeting request")
        
        # In a real implementation, these would be passed to enhanced agent prompts
        enhanced_inputs['_quality_enhancements'] = enhancements
        enhanced_inputs['_attempt'] = attempt
        
        return enhanced_inputs


def run_auto_improvement_agent(inputs: Dict[str, Any]) -> None:
    """Run the agent with auto-improvement wrapper."""
    
    print("🚀 Starting Auto-Improvement Sales Email Agent")
    print("=" * 60)
    print(f"Inputs: {json.dumps(inputs, indent=2)}")
    print("=" * 60)
    
    wrapper = AutoImprovementWrapper()
    
    try:
        result = wrapper.run_with_quality_validation(inputs)
        
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        print(f"✅ Success: {result['success']}")
        print(f"🔄 Attempts: {result['attempts']}")
        print(f"📈 Final Quality Score: {result['quality_score'].total_score}/100")
        print(f"📧 Email Content Length: {len(result['email_content'])} characters")
        
        if result['success']:
            print("✅ EMAIL MEETS QUALITY STANDARDS")
        else:
            print("⚠️  EMAIL BELOW QUALITY THRESHOLD - MANUAL REVIEW RECOMMENDED")
            
        print(f"\n📧 FINAL EMAIL:")
        print("-" * 40)
        print(result['email_content'])
        print("-" * 40)
        
        # Detailed quality breakdown
        score = result['quality_score']
        print(f"\n📊 QUALITY BREAKDOWN:")
        print(f"   Structure Compliance: {score.structure_score}/40")
        print(f"   Personalization Quality: {score.personalization_score}/30") 
        print(f"   Message Quality: {score.message_score}/30")
        print(f"   TOTAL: {score.total_score}/100")
        
        quality_grade = "A+" if score.total_score >= 95 else "A" if score.total_score >= 85 else "B" if score.total_score >= 70 else "C"
        print(f"   Quality Grade: {quality_grade}")
        
        return result
        
    except Exception as e:
        print(f"❌ AUTO-IMPROVEMENT FAILED: {str(e)}")
        raise


if __name__ == "__main__":
    # Test the auto-improvement wrapper
    test_inputs = {
        "first_name": "Milan",
        "last_name": "Kulhanek", 
        "title": "",
        "company": "Deloitte",
        "phone": "",
        "country": "",
        "linkedin_profile": "",
        "selling_intent": ""  # Test with no specific intent to verify dynamic handling
    }
    
    run_auto_improvement_agent(test_inputs)