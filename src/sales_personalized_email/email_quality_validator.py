#!/usr/bin/env python3
"""
Email Quality Validator for Auto-Improving Sales Email Agent
Implements the 100-point quality scoring system from AUTO_IMPROVEMENT_SPEC.md
"""

import re
import json
from typing import Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class QualityScore:
    total_score: int
    structure_score: int
    personalization_score: int
    message_score: int
    intent_score: int
    details: Dict[str, Any]
    

class EmailQualityValidator:
    """
    Validates email quality according to the 100-point scoring system.
    
    Scoring breakdown:
    - Structure Compliance: 35 points
    - Personalization Quality: 25 points  
    - Message Quality: 25 points
    - Selling Intent Compliance: 15 points (CRITICAL)
    """
    
    def __init__(self):
        self.keboola_use_cases = {
            'financial': {'metric': '70% reduction in FP&A reporting time', 'customer': 'Home Credit'},
            'retail': {'metric': '80% reduction in manual data processing', 'customer': 'Rohlik'},
            'logistics': {'metric': 'unified data across 8 countries', 'customer': 'P3 Logistic Parks'},
            'manufacturing': {'metric': '50% reduction in data tool costs', 'customer': 'manufacturing clients'},
            'technology': {'metric': 'launch analytics projects in days vs months', 'customer': 'tech companies'}
        }
    
    def validate_email(self, email_content: str, research_data: Dict, inputs: Dict) -> QualityScore:
        """Main validation function that calculates total quality score."""
        
        structure_score = self._check_structure_compliance(email_content, research_data, inputs)
        personalization_score = self._check_personalization_quality(email_content, research_data, inputs)
        message_score = self._check_message_quality(email_content, inputs)
        intent_score = self._check_selling_intent_compliance(email_content, inputs)
        
        total_score = structure_score['total'] + personalization_score['total'] + message_score['total'] + intent_score['total']
        
        details = {
            'structure': structure_score,
            'personalization': personalization_score,
            'message': message_score,
            'selling_intent': intent_score
        }
        
        return QualityScore(
            total_score=total_score,
            structure_score=structure_score['total'],
            personalization_score=personalization_score['total'],
            message_score=message_score['total'],
            intent_score=intent_score['total'],
            details=details
        )
    
    def _check_structure_compliance(self, email: str, research_data: Dict, inputs: Dict) -> Dict:
        """Structure Compliance: 35 points total"""
        score_details = {}
        total_score = 0
        
        # First Name Capitalized (5 points)
        first_name = inputs.get('first_name', '').strip()
        if first_name and first_name[0].isupper() and f"Hi {first_name}" in email:
            score_details['first_name'] = 5
            total_score += 5
        else:
            score_details['first_name'] = 0
            
        # Achievement Recognition (10 points)
        achievement_score = self._check_achievement_recognition(email, research_data)
        score_details['achievement'] = achievement_score
        total_score += achievement_score
        
        # Industry Context (10 points) 
        industry_score = self._check_industry_context(email, inputs)
        score_details['industry_context'] = industry_score
        total_score += industry_score
        
        # Value Proposition (8 points) - reduced from 10
        value_prop_score = self._check_value_proposition(email, inputs)
        score_details['value_proposition'] = min(8, value_prop_score)  # Cap at 8
        total_score += min(8, value_prop_score)
        
        # Call-to-Action (5 points)
        cta_score = self._check_call_to_action(email)
        score_details['call_to_action'] = cta_score
        total_score += cta_score
        
        return {'total': total_score, 'details': score_details}
    
    def _check_personalization_quality(self, email: str, research_data: Dict, inputs: Dict) -> Dict:
        """Personalization Quality: 25 points total"""
        score_details = {}
        total_score = 0
        
        # LinkedIn Confidence (12 points) - reduced from 15
        linkedin_confidence = research_data.get('linkedin_confidence', 0)
        if linkedin_confidence >= 90:
            linkedin_score = 12
        elif linkedin_confidence >= 70:
            linkedin_score = 10
        else:
            linkedin_score = 6
        score_details['linkedin_confidence'] = linkedin_score
        total_score += linkedin_score
        
        # Company Research Depth (8 points) - reduced from 10
        company_score = self._check_company_research_depth(email, research_data)
        score_details['company_research'] = min(8, company_score)
        total_score += min(8, company_score)
        
        # Role Relevance (5 points)
        role_score = self._check_role_relevance(email, inputs)
        score_details['role_relevance'] = role_score
        total_score += role_score
        
        return {'total': total_score, 'details': score_details}
    
    def _check_message_quality(self, email: str, inputs: Dict) -> Dict:
        """Message Quality: 25 points total"""
        score_details = {}
        total_score = 0
        
        # Tone & Flow (12 points) - reduced from 15
        tone_score = self._check_tone_and_flow(email)
        score_details['tone_flow'] = min(12, tone_score)
        total_score += min(12, tone_score)
        
        # Length & Crispness (8 points) - reduced from 10
        length_score = self._check_length_and_crispness(email)
        score_details['length_crispness'] = min(8, length_score)
        total_score += min(8, length_score)
        
        # Subject Line Impact (5 points)
        subject_score = self._check_subject_line(email, inputs)
        score_details['subject_line'] = subject_score
        total_score += subject_score
        
        return {'total': total_score, 'details': score_details}
    
    def _check_selling_intent_compliance(self, email: str, inputs: Dict) -> Dict:
        """CRITICAL: Selling Intent Compliance: 15 points total"""
        score_details = {}
        total_score = 0
        
        selling_intent = inputs.get('selling_intent', '').lower().strip()
        email_lower = email.lower()
        
        if not selling_intent:
            # No specific intent provided - generic approach is acceptable
            score_details['intent_specified'] = True
            score_details['keyword_coverage'] = 15  # Full points for no specific requirements
            return {'total': 15, 'details': score_details}
        
        # Extract intent keywords
        intent_keywords = [word for word in selling_intent.split() if len(word) > 2]  # Skip short words
        
        # 1. Keyword Coverage (8 points)
        keywords_found = sum(1 for keyword in intent_keywords if keyword in email_lower)
        keyword_coverage = keywords_found / len(intent_keywords) if intent_keywords else 0
        
        if keyword_coverage >= 0.8:  # 80% of keywords present
            keyword_score = 8
        elif keyword_coverage >= 0.6:  # 60% of keywords present  
            keyword_score = 6
        elif keyword_coverage >= 0.4:  # 40% of keywords present
            keyword_score = 4
        elif keyword_coverage >= 0.2:  # 20% of keywords present
            keyword_score = 2
        else:
            keyword_score = 0
        
        score_details['keyword_coverage'] = keyword_score
        total_score += keyword_score
        
        # 2. Specific Use Case Focus (5 points)
        use_case_score = 0
        if 'coffee machine' in selling_intent:
            if 'coffee' in email_lower:
                use_case_score += 2
            if any(term in email_lower for term in ['facilities', 'consumption', 'maintenance', 'machine']):
                use_case_score += 2
            if any(term in email_lower for term in ['predictive', 'analytics', 'monitoring']):
                use_case_score += 1
        elif 'crm' in selling_intent:
            if 'crm' in email_lower:
                use_case_score += 3
            if any(term in email_lower for term in ['customer', 'segmentation', 'lead scoring']):
                use_case_score += 2
        elif 'supply chain' in selling_intent:
            if any(term in email_lower for term in ['supply chain', 'logistics', 'inventory']):
                use_case_score += 3
            if any(term in email_lower for term in ['optimization', 'visibility', 'tracking']):
                use_case_score += 2
        else:
            # Generic intent - check for relevant business context
            if any(keyword in email_lower for keyword in intent_keywords):
                use_case_score = 3
        
        score_details['use_case_focus'] = min(5, use_case_score)
        total_score += min(5, use_case_score)
        
        # 3. Avoid Generic Data Platform Messaging When Specific Intent Given (2 points)
        generic_penalty = 0
        if selling_intent and 'coffee machine' in selling_intent:
            # Strong penalty for generic data platform messaging when coffee machine intent specified
            if 'data platform' in email_lower and 'coffee' not in email_lower:
                generic_penalty = -3
            elif any(term in email_lower for term in ['generic data', 'data transformation', 'analytics platform']) and 'coffee' not in email_lower:
                generic_penalty = -2
        
        score_details['generic_penalty'] = generic_penalty
        total_score += generic_penalty
        
        # Ensure minimum 0 points
        total_score = max(0, total_score)
        
        return {'total': total_score, 'details': score_details}
    
    def _check_achievement_recognition(self, email: str, research_data: Dict) -> int:
        """Check if email contains achievement recognition (10 points)"""
        achievements = research_data.get('achievements', [])
        linkedin_confidence = research_data.get('linkedin_confidence', 0)
        
        achievement_keywords = ['congratulations', 'impressive', 'notable', 'achievement', 'success', 'proud', 'recognized']
        
        if linkedin_confidence >= 70:
            # Should have specific achievement
            if any(keyword in email.lower() for keyword in achievement_keywords) and achievements:
                return 10 if any(ach.lower() in email.lower() for ach in achievements[:3]) else 8
            else:
                return 4  # Missing specific achievement for high confidence
        else:
            # Generic pleasing acceptable for low confidence
            if any(keyword in email.lower() for keyword in achievement_keywords):
                return 7
            else:
                return 3
    
    def _check_industry_context(self, email: str, inputs: Dict) -> int:
        """Check if email contains Keboola industry use case (10 points)"""
        company = inputs.get('company', '').lower()
        
        # Check for Keboola customer mentions
        keboola_customers = ['home credit', 'rohlik', 'p3 logistic', 'brix']
        if any(customer in email.lower() for customer in keboola_customers):
            return 10
        
        # Check for industry-specific metrics
        industry_metrics = ['70%', '80%', '50%', 'reduction', 'unified data', 'days vs months']
        if any(metric in email.lower() for metric in industry_metrics):
            return 8
        
        # Generic data platform mention
        data_keywords = ['data platform', 'data stack', 'data operations', 'analytics']
        if any(keyword in email.lower() for keyword in data_keywords):
            return 5
        
        return 0
    
    def _check_value_proposition(self, email: str, inputs: Dict) -> int:
        """Check if email contains clear value proposition (10 points)"""
        company = inputs.get('company', '')
        
        # Company-specific value prop
        if company.lower() in email.lower():
            value_keywords = ['help you', 'achieve similar', 'opportunities', 'optimize', 'streamline']
            if any(keyword in email.lower() for keyword in value_keywords):
                return 10
        
        # Generic but relevant value prop
        generic_value = ['data costs', 'efficiency', 'operations', 'similar results']
        if any(keyword in email.lower() for keyword in generic_value):
            return 6
        
        return 0
    
    def _check_call_to_action(self, email: str) -> int:
        """Check for clear meeting request CTA (5 points)"""
        cta_patterns = [
            r'15[-\s]?minute call',
            r'brief call',
            r'quick call', 
            r'demo',
            r'consultation',
            r'meeting',
            r'discuss',
            r'explore'
        ]
        
        if any(re.search(pattern, email.lower()) for pattern in cta_patterns):
            return 5
        return 0
    
    def _check_company_research_depth(self, email: str, research_data: Dict) -> int:
        """Check depth of company research (10 points)"""
        company_info = research_data.get('company_achievements', [])
        
        if len(company_info) >= 2:
            return 10
        elif len(company_info) == 1:
            return 7
        elif 'impressive work' in email.lower() or 'doing well' in email.lower():
            return 4
        return 0
    
    def _check_role_relevance(self, email: str, inputs: Dict) -> int:
        """Check if messaging matches role type (5 points)"""
        title = inputs.get('title', '').lower()
        
        technical_roles = ['cto', 'engineer', 'developer', 'architect', 'technical', 'data']
        business_roles = ['ceo', 'cmo', 'vp', 'director', 'manager', 'head']
        
        technical_keywords = ['technical', 'integration', 'api', 'automation', 'platform']
        business_keywords = ['business', 'roi', 'efficiency', 'costs', 'revenue']
        
        if any(role in title for role in technical_roles):
            if any(keyword in email.lower() for keyword in technical_keywords):
                return 5
        elif any(role in title for role in business_roles):
            if any(keyword in email.lower() for keyword in business_keywords):
                return 5
        else:
            # Generic role - accept either approach
            if any(keyword in email.lower() for keyword in technical_keywords + business_keywords):
                return 4
        
        return 2  # Default for reasonable messaging
    
    def _check_tone_and_flow(self, email: str) -> int:
        """Check professional tone and flow (15 points)"""
        score = 0
        
        # Professional greeting
        if re.search(r'Hi [A-Z][a-z]+,', email):
            score += 3
        
        # Smooth transitions
        transition_words = ['given', 'since', 'because', 'therefore', 'recently', 'we helped']
        if any(word in email.lower() for word in transition_words):
            score += 4
        
        # Professional closing
        if re.search(r'Best regards|Best|Regards|Sincerely', email):
            score += 3
        
        # Conversational but professional tone
        conversational = ['I believe', 'would you', 'I noticed', 'given your']
        if any(phrase in email.lower() for phrase in conversational):
            score += 5
        
        return min(score, 15)
    
    def _check_length_and_crispness(self, email: str) -> int:
        """Check email length and crispness (10 points)"""
        words = len(email.split())
        paragraphs = len([p for p in email.split('\n\n') if p.strip()])
        
        # Word count: 120-180 words ideal
        if 120 <= words <= 180:
            word_score = 5
        elif 100 <= words <= 220:
            word_score = 3
        else:
            word_score = 1
        
        # Paragraph count: 4-6 paragraphs ideal
        if 4 <= paragraphs <= 6:
            para_score = 5
        elif 3 <= paragraphs <= 7:
            para_score = 3
        else:
            para_score = 1
        
        return word_score + para_score
    
    def _check_subject_line(self, email: str, inputs: Dict) -> int:
        """Check subject line quality (5 points)"""
        lines = email.strip().split('\n')
        subject_line = ''
        
        for line in lines:
            if line.startswith('Subject:'):
                subject_line = line.replace('Subject:', '').strip()
                break
        
        if not subject_line:
            return 0
        
        score = 0
        first_name = inputs.get('first_name', '')
        company = inputs.get('company', '')
        
        # Personalized elements
        if first_name in subject_line:
            score += 2
        if company in subject_line:
            score += 1
        
        # Value proposition in subject
        value_words = ['50%', '70%', '80%', 'cut costs', 'reduce', 'data']
        if any(word in subject_line.lower() for word in value_words):
            score += 2
        
        return min(score, 5)
    
    def should_regenerate(self, score: QualityScore) -> Tuple[bool, str]:
        """Determine if email should be regenerated based on score"""
        if score.total_score < 70:
            return True, "Low quality score - immediate regeneration required"
        elif score.total_score < 85:
            return True, "Medium quality score - single optimization attempt"
        else:
            return False, "Quality score acceptable"
    
    def get_improvement_suggestions(self, score: QualityScore) -> Dict[str, str]:
        """Generate specific improvement suggestions based on score breakdown"""
        suggestions = {}
        
        if score.structure_score < 32:  # 80% of 40 points
            suggestions['structure'] = "Improve email structure - ensure proper greeting, achievement recognition, industry context, value proposition, and CTA"
        
        if score.personalization_score < 24:  # 80% of 30 points
            suggestions['personalization'] = "Enhance personalization - improve LinkedIn research and company-specific context"
        
        if score.message_score < 24:  # 80% of 30 points
            suggestions['message'] = "Improve message quality - work on tone, flow, length and subject line"
        
        # Specific detailed suggestions
        details = score.details
        
        if details['structure']['details'].get('first_name', 0) == 0:
            suggestions['first_name'] = "Ensure first name is capitalized and properly formatted in greeting"
        
        if details['structure']['details'].get('achievement', 0) < 7:
            suggestions['achievement'] = "Add specific achievement recognition or improve generic pleasing message"
        
        if details['structure']['details'].get('industry_context', 0) < 8:
            suggestions['industry_context'] = "Include specific Keboola customer use case from similar industry"
        
        if details['structure']['details'].get('call_to_action', 0) == 0:
            suggestions['cta'] = "Add clear meeting request call-to-action"
        
        return suggestions


def validate_and_improve_email(email_content: str, research_data: Dict, inputs: Dict, max_attempts: int = 3) -> Tuple[str, QualityScore, int]:
    """
    Main function to validate email and suggest improvements.
    Returns: (email_content, final_score, attempts_made)
    """
    validator = EmailQualityValidator()
    
    for attempt in range(max_attempts):
        score = validator.validate_email(email_content, research_data, inputs)
        should_regen, reason = validator.should_regenerate(score)
        
        if not should_regen:
            return email_content, score, attempt + 1
        
        if attempt < max_attempts - 1:
            # Generate improvement suggestions for next attempt
            suggestions = validator.get_improvement_suggestions(score)
            print(f"Attempt {attempt + 1}: Score {score.total_score}/100 - {reason}")
            print("Improvement suggestions:", suggestions)
            # In a real implementation, this would trigger agent re-generation with enhanced prompts
            
    return email_content, score, max_attempts


if __name__ == "__main__":
    # Test the validator
    sample_email = """Subject: Congratulations on Partnership - How P3 Unified Data Across 8 Countries

Hi Milan,

Congratulations on your recent promotion to Partner at Deloitte! Your leadership in automotive and supply chain is impressive.

We recently helped P3 Logistic Parks unify data across 8 countries using our data platform. This eliminated data silos and improved operational visibility.

Given your role at Deloitte and focus on supply chain optimization, I believe we could help you achieve similar results for your clients.

Would you be open to a brief 15-minute call to explore how this might apply to your consulting practice?

Best regards,
Sarah"""

    sample_research = {
        'linkedin_confidence': 95,
        'achievements': ['recent promotion to Partner', 'automotive leader'],
        'company_achievements': ['Deloitte consulting', 'supply chain expertise']
    }
    
    sample_inputs = {
        'first_name': 'Milan',
        'company': 'Deloitte',
        'title': 'Partner'
    }
    
    validator = EmailQualityValidator()
    score = validator.validate_email(sample_email, sample_research, sample_inputs)
    
    print(f"Total Score: {score.total_score}/100")
    print(f"Structure: {score.structure_score}/40")
    print(f"Personalization: {score.personalization_score}/30") 
    print(f"Message: {score.message_score}/30")
    print(f"Details: {json.dumps(score.details, indent=2)}")