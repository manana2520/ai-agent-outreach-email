#!/usr/bin/env python3
"""
LLM-Powered Failure Analyzer

Analyzes test failures to identify root causes in agent/task prompts.
Uses LLM to generate sophisticated failure analysis and improvement recommendations.
"""

import os
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import openai

from sales_personalized_email.test_runner import TestResult, TestSuiteResults


@dataclass
class FailurePattern:
    """Identified failure pattern"""
    pattern_type: str
    frequency: int
    percentage: float
    affected_agent: str
    affected_task: str
    example_failures: List[str]
    root_cause: str
    severity: str  # 'critical', 'high', 'medium', 'low'


@dataclass
class AnalysisReport:
    """Comprehensive failure analysis report"""
    total_failures: int
    failure_patterns: List[FailurePattern]
    agent_weaknesses: Dict[str, List[str]]
    task_weaknesses: Dict[str, List[str]]
    priority_fixes: List[str]
    summary: str


class FailureAnalyzer:
    """
    Uses LLM to analyze test failures and identify prompt improvements needed.
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize failure analyzer.

        Args:
            model: OpenAI model to use for analysis (default: gpt-4)
        """
        self.model = model
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        # Check if using OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            openai.api_base = "https://openrouter.ai/api/v1"
            openai.api_key = os.getenv('OPENROUTER_API_KEY')
            self.model = "openai/gpt-4-turbo"  # Use through OpenRouter
        else:
            openai.api_key = api_key

    def analyze_failures(
        self,
        test_results: TestSuiteResults,
        current_agents_yaml: str,
        current_tasks_yaml: str
    ) -> AnalysisReport:
        """
        Analyze all failures and generate comprehensive report.

        Args:
            test_results: Test suite results with failures
            current_agents_yaml: Current agents.yaml content
            current_tasks_yaml: Current tasks.yaml content

        Returns:
            AnalysisReport with detailed analysis and recommendations
        """

        print(f"\n🔍 Analyzing {test_results.num_failures} failures...")

        # Group failures by pattern
        failure_patterns = self._identify_failure_patterns(test_results)

        # Analyze with LLM
        agent_weaknesses, task_weaknesses, priority_fixes, summary = self._llm_analyze(
            failure_patterns,
            test_results.failures,
            current_agents_yaml,
            current_tasks_yaml
        )

        report = AnalysisReport(
            total_failures=test_results.num_failures,
            failure_patterns=failure_patterns,
            agent_weaknesses=agent_weaknesses,
            task_weaknesses=task_weaknesses,
            priority_fixes=priority_fixes,
            summary=summary
        )

        self._print_report(report)

        return report

    def _identify_failure_patterns(
        self,
        test_results: TestSuiteResults
    ) -> List[FailurePattern]:
        """
        Identify common failure patterns across tests.

        Args:
            test_results: Test suite results

        Returns:
            List of identified failure patterns
        """

        patterns = []
        failures = test_results.failures
        total_failures = len(failures)

        if total_failures == 0:
            return patterns

        # Pattern 1: Intent compliance failures
        intent_failures = [
            f for f in failures
            if f.quality_score and f.quality_score.intent_score < 12
        ]
        if intent_failures:
            patterns.append(FailurePattern(
                pattern_type="intent_compliance",
                frequency=len(intent_failures),
                percentage=len(intent_failures) / total_failures * 100,
                affected_agent="content_personalizer, email_copywriter",
                affected_task="personalize_content_task, write_email_task",
                example_failures=self._extract_examples(intent_failures, 3),
                root_cause="Agents not properly using selling_intent keywords",
                severity="critical"
            ))

        # Pattern 2: Personalization failures
        personalization_failures = [
            f for f in failures
            if f.quality_score and f.quality_score.personalization_score < 20
        ]
        if personalization_failures:
            patterns.append(FailurePattern(
                pattern_type="personalization_weak",
                frequency=len(personalization_failures),
                percentage=len(personalization_failures) / total_failures * 100,
                affected_agent="linkedin_researcher, prospect_researcher",
                affected_task="linkedin_research_task, research_prospect_task",
                example_failures=self._extract_examples(personalization_failures, 3),
                root_cause="Insufficient research or low-confidence findings",
                severity="high"
            ))

        # Pattern 3: Structure failures
        structure_failures = [
            f for f in failures
            if f.quality_score and f.quality_score.structure_score < 28
        ]
        if structure_failures:
            patterns.append(FailurePattern(
                pattern_type="structure_issues",
                frequency=len(structure_failures),
                percentage=len(structure_failures) / total_failures * 100,
                affected_agent="email_copywriter",
                affected_task="write_email_task",
                example_failures=self._extract_examples(structure_failures, 3),
                root_cause="Email structure requirements not followed",
                severity="medium"
            ))

        # Pattern 4: Message quality failures
        message_failures = [
            f for f in failures
            if f.quality_score and f.quality_score.message_score < 20
        ]
        if message_failures:
            patterns.append(FailurePattern(
                pattern_type="message_quality_low",
                frequency=len(message_failures),
                percentage=len(message_failures) / total_failures * 100,
                affected_agent="email_copywriter",
                affected_task="write_email_task",
                example_failures=self._extract_examples(message_failures, 3),
                root_cause="Poor tone, length, or subject line quality",
                severity="medium"
            ))

        # Pattern 5: CTA failures
        cta_failures = [
            f for f in failures
            if 'call-to-action' in ' '.join(f.critical_failures).lower()
        ]
        if cta_failures:
            patterns.append(FailurePattern(
                pattern_type="missing_cta",
                frequency=len(cta_failures),
                percentage=len(cta_failures) / total_failures * 100,
                affected_agent="email_copywriter",
                affected_task="write_email_task",
                example_failures=self._extract_examples(cta_failures, 3),
                root_cause="Missing or weak call-to-action",
                severity="high"
            ))

        return patterns

    def _extract_examples(self, failures: List[TestResult], num_examples: int) -> List[str]:
        """Extract example failure descriptions"""
        examples = []
        for failure in failures[:num_examples]:
            example = f"Prospect: {failure.prospect_input['first_name']} {failure.prospect_input['last_name']} at {failure.prospect_input['company']}"
            if failure.quality_score:
                example += f" | Score: {failure.quality_score.total_score}/100"
            if failure.critical_failures:
                example += f" | Issues: {', '.join(failure.critical_failures[:2])}"
            examples.append(example)
        return examples

    def _llm_analyze(
        self,
        failure_patterns: List[FailurePattern],
        failures: List[TestResult],
        current_agents_yaml: str,
        current_tasks_yaml: str
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str], str]:
        """
        Use LLM to perform deep analysis of failures.

        Args:
            failure_patterns: Identified failure patterns
            failures: All failure test results
            current_agents_yaml: Current agent prompts
            current_tasks_yaml: Current task descriptions

        Returns:
            Tuple of (agent_weaknesses, task_weaknesses, priority_fixes, summary)
        """

        print("   Using LLM for deep analysis...")

        # Prepare analysis prompt
        prompt = self._build_analysis_prompt(
            failure_patterns,
            failures[:5],  # Top 5 failures
            current_agents_yaml,
            current_tasks_yaml
        )

        try:
            # Call LLM
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert prompt engineer analyzing AI agent failures to recommend prompt improvements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            analysis_text = response.choices[0].message.content

            # Parse LLM response
            agent_weaknesses, task_weaknesses, priority_fixes, summary = self._parse_llm_response(
                analysis_text
            )

            return agent_weaknesses, task_weaknesses, priority_fixes, summary

        except Exception as e:
            print(f"   ⚠️  LLM analysis failed: {e}")
            # Fallback to rule-based analysis
            return self._fallback_analysis(failure_patterns)

    def _build_analysis_prompt(
        self,
        failure_patterns: List[FailurePattern],
        example_failures: List[TestResult],
        agents_yaml: str,
        tasks_yaml: str
    ) -> str:
        """Build comprehensive analysis prompt for LLM"""

        patterns_str = "\n".join([
            f"- {p.pattern_type}: {p.frequency} failures ({p.percentage:.0f}%) - {p.root_cause}"
            for p in failure_patterns
        ])

        failures_str = "\n".join([
            f"- {f.prospect_input['first_name']} at {f.prospect_input['company']}: "
            f"Score {f.quality_score.total_score if f.quality_score else 'N/A'}/100, "
            f"Issues: {', '.join(f.critical_failures[:2])}"
            for f in example_failures
        ])

        prompt = f"""You are analyzing failures in a multi-agent sales email generation system.

FAILURE PATTERNS IDENTIFIED:
{patterns_str}

EXAMPLE FAILURES:
{failures_str}

CURRENT AGENT PROMPTS (agents.yaml):
```yaml
{agents_yaml[:2000]}  # Truncated for context
```

CURRENT TASK DESCRIPTIONS (tasks.yaml):
```yaml
{tasks_yaml[:2000]}  # Truncated for context
```

Please analyze these failures and provide:

1. AGENT WEAKNESSES: Which agent prompts are unclear, missing instructions, or contradictory?
   Format as: agent_name: [weakness1, weakness2, ...]

2. TASK WEAKNESSES: Which task descriptions need strengthening or clarification?
   Format as: task_name: [weakness1, weakness2, ...]

3. PRIORITY FIXES: What are the top 5 most important changes to make?
   Format as numbered list

4. SUMMARY: Brief 2-3 sentence summary of root causes and recommended approach

Format your response exactly as:

AGENT WEAKNESSES:
linkedin_researcher: [weakness1, weakness2]
prospect_researcher: [weakness1]
...

TASK WEAKNESSES:
linkedin_research_task: [weakness1, weakness2]
...

PRIORITY FIXES:
1. Fix1
2. Fix2
...

SUMMARY:
Your summary here.
"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Tuple[Dict, Dict, List[str], str]:
        """Parse structured LLM response"""

        agent_weaknesses = {}
        task_weaknesses = {}
        priority_fixes = []
        summary = ""

        current_section = None
        lines = response_text.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('AGENT WEAKNESSES:'):
                current_section = 'agents'
            elif line.startswith('TASK WEAKNESSES:'):
                current_section = 'tasks'
            elif line.startswith('PRIORITY FIXES:'):
                current_section = 'priorities'
            elif line.startswith('SUMMARY:'):
                current_section = 'summary'
            elif line:
                if current_section == 'agents' and ':' in line:
                    agent, weaknesses = line.split(':', 1)
                    agent_weaknesses[agent.strip()] = [weaknesses.strip()]
                elif current_section == 'tasks' and ':' in line:
                    task, weaknesses = line.split(':', 1)
                    task_weaknesses[task.strip()] = [weaknesses.strip()]
                elif current_section == 'priorities' and line[0].isdigit():
                    priority_fixes.append(line.split('.', 1)[1].strip() if '.' in line else line)
                elif current_section == 'summary':
                    summary += line + " "

        return agent_weaknesses, task_weaknesses, priority_fixes, summary.strip()

    def _fallback_analysis(
        self,
        failure_patterns: List[FailurePattern]
    ) -> Tuple[Dict, Dict, List[str], str]:
        """Fallback rule-based analysis if LLM fails"""

        agent_weaknesses = {}
        task_weaknesses = {}
        priority_fixes = []

        for pattern in failure_patterns:
            if pattern.pattern_type == 'intent_compliance':
                agent_weaknesses['content_personalizer'] = [
                    "Not consistently using selling_intent keywords",
                    "May be using generic messaging instead of specific use case"
                ]
                agent_weaknesses['email_copywriter'] = [
                    "Not enforcing selling_intent keywords in subject and body",
                    "Allowing generic data platform messaging when specific intent provided"
                ]
                priority_fixes.append("Strengthen selling_intent enforcement in content_personalizer and email_copywriter")

            elif pattern.pattern_type == 'personalization_weak':
                agent_weaknesses['linkedin_researcher'] = [
                    "May not be finding LinkedIn profiles consistently",
                    "Confidence threshold may be too conservative"
                ]
                priority_fixes.append("Improve LinkedIn research reliability and confidence assessment")

            elif pattern.pattern_type == 'missing_cta':
                agent_weaknesses['email_copywriter'] = [
                    "Not consistently including strong CTAs",
                    "May be using weak permission-seeking language"
                ]
                priority_fixes.append("Add explicit CTA requirements with examples to email_copywriter")

        summary = f"Found {len(failure_patterns)} failure patterns. Primary issues are {', '.join([p.pattern_type for p in failure_patterns[:3]])}."

        return agent_weaknesses, task_weaknesses, priority_fixes, summary

    def _print_report(self, report: AnalysisReport):
        """Print formatted analysis report"""

        print(f"\n📋 FAILURE ANALYSIS REPORT")
        print("=" * 70)
        print(f"Total Failures: {report.total_failures}")
        print(f"\nSummary: {report.summary}")

        print(f"\n🔴 FAILURE PATTERNS:")
        for pattern in sorted(report.failure_patterns, key=lambda p: p.frequency, reverse=True):
            print(f"\n   {pattern.pattern_type} ({pattern.severity.upper()})")
            print(f"   Frequency: {pattern.frequency}/{report.total_failures} ({pattern.percentage:.0f}%)")
            print(f"   Affected: {pattern.affected_agent}")
            print(f"   Root Cause: {pattern.root_cause}")

        print(f"\n⚡ TOP PRIORITY FIXES:")
        for i, fix in enumerate(report.priority_fixes[:5], 1):
            print(f"   {i}. {fix}")

        print(f"\n🎯 AGENT WEAKNESSES:")
        for agent, weaknesses in report.agent_weaknesses.items():
            print(f"   {agent}:")
            for weakness in weaknesses:
                print(f"      - {weakness}")

        if report.task_weaknesses:
            print(f"\n📝 TASK WEAKNESSES:")
            for task, weaknesses in report.task_weaknesses.items():
                print(f"   {task}:")
                for weakness in weaknesses:
                    print(f"      - {weakness}")


if __name__ == "__main__":
    print("🧪 Failure Analyzer Test")
    print("Note: This module requires test results to analyze.")
    print("Run test_runner.py first to generate test results.")
