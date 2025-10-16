#!/usr/bin/env python3
"""
Comprehensive Test Runner for Auto-Improvement System

Executes crew with test prospects and validates outputs against quality criteria.
Provides detailed pass/fail analysis with 95% pass rate target.
"""

import subprocess
import json
import tempfile
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from sales_personalized_email.email_quality_validator import (
    EmailQualityValidator,
    QualityScore
)


@dataclass
class TestResult:
    """Single test execution result"""
    prospect_input: Dict
    passed: bool
    quality_score: Optional[QualityScore]
    output: Optional[Dict]
    critical_failures: List[str]
    execution_time: float
    error: Optional[str] = None


@dataclass
class TestSuiteResults:
    """Complete test suite results"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    avg_quality_score: float
    results: List[TestResult]
    failure_patterns: Dict[str, int]
    timestamp: str

    @property
    def num_failures(self) -> int:
        return self.failed_tests

    @property
    def failures(self) -> List[TestResult]:
        return [r for r in self.results if not r.passed]


class CrewTestRunner:
    """
    Executes crew and validates quality metrics.

    Quality criteria (ALL must pass):
    - Total score >= 85/100
    - Intent compliance (if provided): >= 12/15
    - First name capitalized: True
    - CTA present: score >= 3/5
    - No generic messaging when specific intent provided
    """

    def __init__(self, crew_command: str = "crewai run"):
        self.crew_command = crew_command
        self.validator = EmailQualityValidator()
        self.quality_threshold = 85

    def run_single_test(
        self,
        prospect_input: Dict,
        timeout: int = 180
    ) -> TestResult:
        """
        Run crew with single prospect input and validate output.

        Args:
            prospect_input: Prospect dictionary with keys:
                first_name, last_name, company, title, selling_intent, etc.
            timeout: Execution timeout in seconds (default: 180)

        Returns:
            TestResult with pass/fail and detailed metrics
        """

        start_time = datetime.now()

        try:
            # Execute crew
            output = self._execute_crew(prospect_input, timeout)

            if output is None:
                return TestResult(
                    prospect_input=prospect_input,
                    passed=False,
                    quality_score=None,
                    output=None,
                    critical_failures=["Crew execution failed"],
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error="Crew execution failed or returned no output"
                )

            # Validate output
            quality_score = self._validate_output(output, prospect_input)

            # Check critical failures
            critical_failures = self._check_critical_failures(
                output, prospect_input, quality_score
            )

            # Determine pass/fail
            passed = len(critical_failures) == 0 and quality_score.total_score >= self.quality_threshold

            execution_time = (datetime.now() - start_time).total_seconds()

            return TestResult(
                prospect_input=prospect_input,
                passed=passed,
                quality_score=quality_score,
                output=output,
                critical_failures=critical_failures,
                execution_time=execution_time
            )

        except Exception as e:
            return TestResult(
                prospect_input=prospect_input,
                passed=False,
                quality_score=None,
                output=None,
                critical_failures=[f"Exception: {str(e)}"],
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )

    def run_test_suite(
        self,
        prospects: List[Dict],
        target_pass_rate: float = 0.95
    ) -> TestSuiteResults:
        """
        Run all prospects and aggregate results.

        Args:
            prospects: List of prospect dictionaries
            target_pass_rate: Target pass rate (default: 0.95)

        Returns:
            TestSuiteResults with comprehensive analysis
        """

        print(f"\n🚀 Running test suite with {len(prospects)} prospects")
        print(f"   Target pass rate: {target_pass_rate*100:.0f}%")
        print(f"   Quality threshold: {self.quality_threshold}/100")
        print("=" * 70)

        results = []

        for i, prospect in enumerate(prospects, 1):
            print(f"\n[{i}/{len(prospects)}] Testing: {prospect['first_name']} {prospect['last_name']} at {prospect['company']}")

            result = self.run_single_test(prospect)

            if result.passed:
                print(f"  ✅ PASS - Score: {result.quality_score.total_score}/100")
            else:
                print(f"  ❌ FAIL - Score: {result.quality_score.total_score if result.quality_score else 'N/A'}/100")
                if result.critical_failures:
                    print(f"  ⚠️  Critical failures:")
                    for failure in result.critical_failures[:3]:  # Show top 3
                        print(f"     - {failure}")

            results.append(result)

        # Calculate aggregate metrics
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = len(results) - passed_tests
        pass_rate = passed_tests / len(results) if results else 0.0

        # Calculate average quality score
        quality_scores = [r.quality_score.total_score for r in results if r.quality_score]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        # Analyze failure patterns
        failure_patterns = self._analyze_failure_patterns(results)

        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 70)
        print(f"Total tests: {len(results)}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Pass rate: {pass_rate*100:.1f}% (Target: {target_pass_rate*100:.0f}%)")
        print(f"Average quality score: {avg_quality_score:.1f}/100")

        if pass_rate >= target_pass_rate:
            print(f"\n🎉 SUCCESS! Achieved target pass rate!")
        else:
            shortfall = target_pass_rate - pass_rate
            print(f"\n⚠️  BELOW TARGET by {shortfall*100:.1f} percentage points")

        print("\n🔍 Top Failure Patterns:")
        for pattern, count in sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = (count / failed_tests * 100) if failed_tests > 0 else 0
            print(f"   - {pattern}: {count}/{failed_tests} ({percentage:.0f}%)")

        return TestSuiteResults(
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            pass_rate=pass_rate,
            avg_quality_score=avg_quality_score,
            results=results,
            failure_patterns=failure_patterns,
            timestamp=datetime.now().isoformat()
        )

    def _execute_crew(
        self,
        prospect_input: Dict,
        timeout: int
    ) -> Optional[Dict]:
        """
        Execute crew with prospect input using crewai run.

        Args:
            prospect_input: Prospect data
            timeout: Execution timeout in seconds

        Returns:
            Parsed crew output or None if failed
        """

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(prospect_input, f)
            input_file = f.name

        try:
            # Build command
            # Use python -m to run the crew
            cmd = [
                'python', '-m', 'sales_personalized_email.main',
                'kickoff',
                '--first_name', prospect_input['first_name'],
                '--last_name', prospect_input['last_name'],
                '--company', prospect_input['company'],
            ]

            # Add optional fields
            if prospect_input.get('title'):
                cmd.extend(['--title', prospect_input['title']])
            if prospect_input.get('phone'):
                cmd.extend(['--phone', prospect_input['phone']])
            if prospect_input.get('country'):
                cmd.extend(['--country', prospect_input['country']])
            if prospect_input.get('linkedin_profile'):
                cmd.extend(['--linkedin_profile', prospect_input['linkedin_profile']])
            if prospect_input.get('selling_intent'):
                cmd.extend(['--selling_intent', prospect_input['selling_intent']])

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            # Parse output
            output = self._parse_crew_output(result.stdout)
            return output

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Timeout after {timeout}s")
            return None
        except Exception as e:
            print(f"  ⚠️  Execution error: {e}")
            return None
        finally:
            # Clean up temp file
            if os.path.exists(input_file):
                os.unlink(input_file)

    def _parse_crew_output(self, stdout: str) -> Optional[Dict]:
        """
        Parse crew output to extract PersonalizedEmail result.

        Args:
            stdout: Raw stdout from crew execution

        Returns:
            Parsed output dictionary or None
        """

        try:
            # Look for JSON output in stdout
            # CrewAI typically outputs result as JSON at the end

            lines = stdout.split('\n')

            # Find JSON output (typically last substantial block)
            json_str = None
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line.startswith('{') and 'subject_line' in line:
                    # Found JSON output
                    json_str = line
                    break

            if json_str:
                return json.loads(json_str)

            # Alternative: Look for structured output markers
            output_dict = {}
            in_output = False

            for line in lines:
                if 'subject_line:' in line.lower():
                    in_output = True
                    output_dict['subject_line'] = line.split(':', 1)[1].strip()
                elif 'email_body:' in line.lower() and in_output:
                    output_dict['email_body'] = line.split(':', 1)[1].strip()
                elif 'follow_up_notes:' in line.lower() and in_output:
                    output_dict['follow_up_notes'] = line.split(':', 1)[1].strip()

            if output_dict.get('subject_line') and output_dict.get('email_body'):
                return output_dict

            return None

        except Exception as e:
            print(f"  ⚠️  Parse error: {e}")
            return None

    def _validate_output(
        self,
        output: Dict,
        prospect_input: Dict
    ) -> QualityScore:
        """
        Validate crew output using EmailQualityValidator.

        Args:
            output: Crew output dictionary
            prospect_input: Original prospect input

        Returns:
            QualityScore with detailed metrics
        """

        # Construct full email for validation
        subject_line = output.get('subject_line', '')
        email_body = output.get('email_body', '')
        full_email = f"Subject: {subject_line}\n\n{email_body}"

        # Simulate research data based on what crew should have found
        research_data = {
            'linkedin_confidence': 80,  # Assume reasonable confidence
            'achievements': [],  # Would be extracted from output
            'company_achievements': []
        }

        # If LinkedIn profile was validated in output, increase confidence
        if output.get('validated_linkedin_profile'):
            research_data['linkedin_confidence'] = 95

        # Run validation
        quality_score = self.validator.validate_email(
            full_email,
            research_data,
            prospect_input
        )

        return quality_score

    def _check_critical_failures(
        self,
        output: Dict,
        prospect_input: Dict,
        quality_score: QualityScore
    ) -> List[str]:
        """
        Check for critical failures that cause automatic test failure.

        Critical failures:
        - Intent compliance < 12/15 (when intent provided)
        - First name not capitalized
        - No CTA (score < 3)
        - Generic messaging when specific intent provided
        - Missing required output fields

        Args:
            output: Crew output
            prospect_input: Input data
            quality_score: Quality score from validation

        Returns:
            List of critical failure messages
        """

        failures = []

        # Check required fields
        if not output.get('subject_line'):
            failures.append("Missing subject_line")
        if not output.get('email_body'):
            failures.append("Missing email_body")

        # Check first name capitalization
        first_name = prospect_input.get('first_name', '')
        email_body = output.get('email_body', '')
        if first_name and not (f"Hi {first_name}" in email_body or f"{first_name}," in email_body):
            failures.append("First name not properly capitalized in greeting")

        # Check intent compliance (CRITICAL)
        selling_intent = prospect_input.get('selling_intent', '').strip()
        if selling_intent and quality_score.intent_score < 12:
            failures.append(f"Intent compliance too low: {quality_score.intent_score}/15 (required: >= 12)")

        # Check CTA
        if quality_score.details['structure']['details'].get('call_to_action', 0) < 3:
            failures.append("Missing or weak call-to-action")

        # Check generic messaging when intent provided
        if selling_intent:
            email_lower = email_body.lower()
            intent_keywords = [w for w in selling_intent.lower().split() if len(w) > 2]
            has_intent_keyword = any(keyword in email_lower for keyword in intent_keywords)

            if not has_intent_keyword:
                failures.append("Generic messaging used despite specific selling_intent provided")

        return failures

    def _analyze_failure_patterns(self, results: List[TestResult]) -> Dict[str, int]:
        """
        Analyze failure patterns across all results.

        Returns:
            Dictionary of failure pattern -> count
        """

        patterns = {}

        for result in results:
            if not result.passed:
                # Categorize failures
                if result.quality_score is None:
                    patterns['execution_failure'] = patterns.get('execution_failure', 0) + 1
                else:
                    # Intent failures
                    if result.quality_score.intent_score < 12:
                        patterns['intent_compliance_low'] = patterns.get('intent_compliance_low', 0) + 1

                    # Structure failures
                    if result.quality_score.structure_score < 28:  # 80% of 35
                        patterns['structure_issues'] = patterns.get('structure_issues', 0) + 1

                    # Personalization failures
                    if result.quality_score.personalization_score < 20:  # 80% of 25
                        patterns['personalization_weak'] = patterns.get('personalization_weak', 0) + 1

                    # Message quality failures
                    if result.quality_score.message_score < 20:  # 80% of 25
                        patterns['message_quality_low'] = patterns.get('message_quality_low', 0) + 1

                # Critical failures
                for failure in result.critical_failures:
                    if 'Intent compliance' in failure:
                        patterns['critical_intent_failure'] = patterns.get('critical_intent_failure', 0) + 1
                    elif 'First name' in failure:
                        patterns['capitalization_error'] = patterns.get('capitalization_error', 0) + 1
                    elif 'call-to-action' in failure:
                        patterns['missing_cta'] = patterns.get('missing_cta', 0) + 1
                    elif 'Generic messaging' in failure:
                        patterns['generic_messaging'] = patterns.get('generic_messaging', 0) + 1

        return patterns


if __name__ == "__main__":
    """
    Test the test runner
    """

    print("🧪 Testing Crew Test Runner")
    print("=" * 70)

    # Create sample test prospect
    test_prospect = {
        'first_name': 'Milan',
        'last_name': 'Kulhanek',
        'title': 'Partner',
        'company': 'Deloitte',
        'phone': '',
        'country': 'Czech Republic',
        'linkedin_profile': '',
        'selling_intent': 'supply chain optimization and visibility'
    }

    runner = CrewTestRunner()

    print("\n📝 Running single test...")
    result = runner.run_single_test(test_prospect)

    print(f"\n✅ Test complete!")
    print(f"   Passed: {result.passed}")
    print(f"   Quality Score: {result.quality_score.total_score if result.quality_score else 'N/A'}/100")
    print(f"   Execution Time: {result.execution_time:.1f}s")

    if result.critical_failures:
        print(f"\n   Critical Failures:")
        for failure in result.critical_failures:
            print(f"     - {failure}")
