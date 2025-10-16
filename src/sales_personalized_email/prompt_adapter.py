#!/usr/bin/env python3
"""
LLM-Powered Prompt Adaptation Engine

Generates improved agent and task prompts based on failure analysis.
Uses LLM to create sophisticated prompt improvements that address root causes.
"""

import os
import yaml
import openai
from typing import Dict, Tuple, List
from dataclasses import dataclass, asdict
from copy import deepcopy

from sales_personalized_email.failure_analyzer import AnalysisReport


@dataclass
class PromptImprovement:
    """Single prompt improvement"""
    target: str  # 'agent' or 'task'
    name: str  # agent/task name
    field: str  # 'role', 'goal', 'backstory', 'description', etc.
    original_text: str
    improved_text: str
    rationale: str


@dataclass
class PromptImprovements:
    """Collection of prompt improvements"""
    improvements: List[PromptImprovement]
    summary: str
    expected_impact: str


class PromptAdapter:
    """
    LLM-powered prompt improvement generator.

    Analyzes failures and generates targeted prompt improvements
    to address root causes while preserving existing functionality.
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize prompt adapter.

        Args:
            model: OpenAI model to use (default: gpt-4)
        """
        self.model = model
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        # Check if using OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            openai.api_base = "https://openrouter.ai/api/v1"
            openai.api_key = os.getenv('OPENROUTER_API_KEY')
            self.model = "openai/gpt-4-turbo"
        else:
            openai.api_key = api_key

    def adapt_prompts(
        self,
        analysis: AnalysisReport,
        current_agents: Dict,
        current_tasks: Dict,
        failure_examples: List
    ) -> PromptImprovements:
        """
        Generate prompt improvements based on failure analysis.

        Args:
            analysis: Failure analysis report
            current_agents: Current agents dictionary from YAML
            current_tasks: Current tasks dictionary from YAML
            failure_examples: Example failure test results

        Returns:
            PromptImprovements with all suggested changes
        """

        print(f"\n🔧 Generating prompt improvements...")

        # Generate improvements using LLM
        improvements = self._llm_generate_improvements(
            analysis,
            current_agents,
            current_tasks,
            failure_examples
        )

        print(f"   Generated {len(improvements.improvements)} improvements")

        self._print_improvements(improvements)

        return improvements

    def apply_improvements(
        self,
        improvements: PromptImprovements,
        agents_yaml_path: str,
        tasks_yaml_path: str
    ) -> Tuple[str, str]:
        """
        Apply improvements to YAML files.

        Args:
            improvements: Prompt improvements to apply
            agents_yaml_path: Path to agents.yaml
            tasks_yaml_path: Path to tasks.yaml

        Returns:
            Tuple of (updated_agents_yaml_string, updated_tasks_yaml_string)
        """

        print(f"\n✏️  Applying {len(improvements.improvements)} improvements...")

        # Load current YAMLs
        with open(agents_yaml_path, 'r') as f:
            agents = yaml.safe_load(f)

        with open(tasks_yaml_path, 'r') as f:
            tasks = yaml.safe_load(f)

        # Apply each improvement
        for improvement in improvements.improvements:
            if improvement.target == 'agent':
                if improvement.name in agents:
                    agents[improvement.name][improvement.field] = improvement.improved_text
                    print(f"   ✓ Updated agent '{improvement.name}' {improvement.field}")
            elif improvement.target == 'task':
                if improvement.name in tasks:
                    tasks[improvement.name][improvement.field] = improvement.improved_text
                    print(f"   ✓ Updated task '{improvement.name}' {improvement.field}")

        # Convert back to YAML strings
        agents_yaml_str = yaml.dump(agents, default_flow_style=False, sort_keys=False, width=120)
        tasks_yaml_str = yaml.dump(tasks, default_flow_style=False, sort_keys=False, width=120)

        # Write back to files
        with open(agents_yaml_path, 'w') as f:
            f.write(agents_yaml_str)

        with open(tasks_yaml_path, 'w') as f:
            f.write(tasks_yaml_str)

        print(f"   ✅ Applied all improvements")

        return agents_yaml_str, tasks_yaml_str

    def _llm_generate_improvements(
        self,
        analysis: AnalysisReport,
        current_agents: Dict,
        current_tasks: Dict,
        failure_examples: List
    ) -> PromptImprovements:
        """
        Use LLM to generate targeted prompt improvements.

        Args:
            analysis: Failure analysis
            current_agents: Current agent definitions
            current_tasks: Current task definitions
            failure_examples: Example failures

        Returns:
            PromptImprovements with generated changes
        """

        print("   Using LLM to generate improvements...")

        # Build improvement prompt
        prompt = self._build_improvement_prompt(
            analysis,
            current_agents,
            current_tasks,
            failure_examples[:3]  # Top 3 examples
        )

        try:
            # Call LLM
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert prompt engineer specializing in improving AI agent prompts to fix specific failure patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            improvements_text = response.choices[0].message.content

            # Parse improvements
            improvements = self._parse_improvements(improvements_text, current_agents, current_tasks)

            return improvements

        except Exception as e:
            print(f"   ⚠️  LLM generation failed: {e}")
            # Fallback to rule-based improvements
            return self._fallback_improvements(analysis, current_agents, current_tasks)

    def _build_improvement_prompt(
        self,
        analysis: AnalysisReport,
        agents: Dict,
        tasks: Dict,
        examples: List
    ) -> str:
        """Build comprehensive improvement generation prompt"""

        patterns_str = "\n".join([
            f"- {p.pattern_type} ({p.severity}): {p.frequency} failures - {p.root_cause}"
            for p in analysis.failure_patterns
        ])

        priority_fixes_str = "\n".join([
            f"{i}. {fix}"
            for i, fix in enumerate(analysis.priority_fixes, 1)
        ])

        agent_names = list(agents.keys())
        task_names = list(tasks.keys())

        prompt = f"""You are improving AI agent prompts based on failure analysis.

FAILURE ANALYSIS:
{analysis.summary}

FAILURE PATTERNS:
{patterns_str}

PRIORITY FIXES NEEDED:
{priority_fixes_str}

CURRENT AGENTS: {', '.join(agent_names)}
CURRENT TASKS: {', '.join(task_names)}

YOUR TASK:
Generate specific prompt improvements to address these failures. For each improvement:
1. Identify which agent or task needs modification
2. Identify which field (backstory, goal, description, expected_output)
3. Provide the improved text
4. Explain the rationale

GUIDELINES:
- Be specific and actionable
- Address root causes, not symptoms
- Preserve existing good functionality
- Use clear, unambiguous language
- Add concrete examples where helpful
- Strengthen critical requirements with "CRITICAL:", "MANDATORY:", etc.
- For intent compliance issues: Add explicit selling_intent enforcement
- For personalization issues: Strengthen research requirements
- For CTA issues: Add CTA examples and requirements

FORMAT YOUR RESPONSE AS:

IMPROVEMENT 1:
Target: agent | task
Name: agent_name or task_name
Field: backstory | goal | description | expected_output
Improved Text:
```
Your improved text here (can be multiple lines)
```
Rationale: Why this change addresses the failure

IMPROVEMENT 2:
...

SUMMARY:
Brief summary of improvements and expected impact.

EXPECTED IMPACT:
Predicted improvement in pass rate and specific metrics.
"""

        return prompt

    def _parse_improvements(
        self,
        improvements_text: str,
        agents: Dict,
        tasks: Dict
    ) -> PromptImprovements:
        """Parse LLM-generated improvements"""

        improvements = []
        current_improvement = {}
        in_improved_text = False
        improved_text_lines = []

        lines = improvements_text.split('\n')

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith('IMPROVEMENT'):
                # Save previous improvement if exists
                if current_improvement and 'improved_text' in current_improvement:
                    improvements.append(PromptImprovement(**current_improvement))
                current_improvement = {}
                in_improved_text = False

            elif line_stripped.startswith('Target:'):
                current_improvement['target'] = line_stripped.split(':', 1)[1].strip().lower()

            elif line_stripped.startswith('Name:'):
                current_improvement['name'] = line_stripped.split(':', 1)[1].strip()

            elif line_stripped.startswith('Field:'):
                current_improvement['field'] = line_stripped.split(':', 1)[1].strip()

            elif line_stripped.startswith('Improved Text:'):
                in_improved_text = True
                improved_text_lines = []

            elif line_stripped.startswith('Rationale:'):
                in_improved_text = False
                current_improvement['improved_text'] = '\n'.join(improved_text_lines).strip()
                current_improvement['rationale'] = line_stripped.split(':', 1)[1].strip()

                # Get original text
                if current_improvement.get('target') == 'agent' and current_improvement.get('name') in agents:
                    current_improvement['original_text'] = agents[current_improvement['name']].get(
                        current_improvement['field'], ''
                    )
                elif current_improvement.get('target') == 'task' and current_improvement.get('name') in tasks:
                    current_improvement['original_text'] = tasks[current_improvement['name']].get(
                        current_improvement['field'], ''
                    )

            elif line_stripped.startswith('SUMMARY:'):
                in_improved_text = False
                # Save last improvement
                if current_improvement and 'improved_text' in current_improvement:
                    improvements.append(PromptImprovement(**current_improvement))
                current_improvement = {}

            elif in_improved_text and not line_stripped.startswith('```'):
                improved_text_lines.append(line)

        # Extract summary and expected impact
        summary = ""
        expected_impact = ""

        in_summary = False
        in_impact = False

        for line in lines:
            if line.strip().startswith('SUMMARY:'):
                in_summary = True
                in_impact = False
            elif line.strip().startswith('EXPECTED IMPACT:'):
                in_impact = True
                in_summary = False
            elif in_summary and line.strip():
                summary += line.strip() + " "
            elif in_impact and line.strip():
                expected_impact += line.strip() + " "

        return PromptImprovements(
            improvements=improvements,
            summary=summary.strip(),
            expected_impact=expected_impact.strip()
        )

    def _fallback_improvements(
        self,
        analysis: AnalysisReport,
        agents: Dict,
        tasks: Dict
    ) -> PromptImprovements:
        """Fallback rule-based improvements if LLM fails"""

        improvements = []

        # Intent compliance improvements
        if any(p.pattern_type == 'intent_compliance' for p in analysis.failure_patterns):
            # Strengthen email_copywriter
            if 'email_copywriter' in agents:
                improvements.append(PromptImprovement(
                    target='agent',
                    name='email_copywriter',
                    field='backstory',
                    original_text=agents['email_copywriter'].get('backstory', ''),
                    improved_text=agents['email_copywriter'].get('backstory', '') +
                    "\n\nCRITICAL SELLING INTENT ENFORCEMENT:\n" +
                    "When selling_intent is provided, you MUST use those EXACT keywords throughout the email.\n" +
                    "Subject line MUST contain keywords from selling_intent.\n" +
                    "Email body MUST mention selling_intent keywords multiple times.\n" +
                    "NO generic data platform messaging when specific intent provided.",
                    rationale="Add explicit selling_intent enforcement to prevent generic messaging"
                ))

        # Personalization improvements
        if any(p.pattern_type == 'personalization_weak' for p in analysis.failure_patterns):
            # Strengthen linkedin_researcher
            if 'linkedin_researcher' in agents:
                improvements.append(PromptImprovement(
                    target='agent',
                    name='linkedin_researcher',
                    field='backstory',
                    original_text=agents['linkedin_researcher'].get('backstory', ''),
                    improved_text=agents['linkedin_researcher'].get('backstory', '') +
                    "\n\nMANDATORY: You MUST return LinkedIn profiles for unique name + company combinations.\n" +
                    "Don't be overly cautious - if the profile clearly matches, return it with high confidence.",
                    rationale="Increase aggressiveness in LinkedIn research"
                ))

        # CTA improvements
        if any(p.pattern_type == 'missing_cta' for p in analysis.failure_patterns):
            # Strengthen email_copywriter CTA requirements
            if 'write_email_task' in tasks:
                improvements.append(PromptImprovement(
                    target='task',
                    name='write_email_task',
                    field='description',
                    original_text=tasks['write_email_task'].get('description', ''),
                    improved_text=tasks['write_email_task'].get('description', '') +
                    "\n\nMANDATORY CTA: Every email MUST end with a strong assumptive call-to-action.\n" +
                    "Examples: 'When's the best time this week for a 15-minute call?'\n" +
                    "FORBIDDEN: Weak CTAs like 'Would you be open to...'",
                    rationale="Add explicit CTA requirements with examples"
                ))

        return PromptImprovements(
            improvements=improvements,
            summary="Applied rule-based improvements for identified failure patterns",
            expected_impact="Improvements should address critical failure patterns"
        )

    def _print_improvements(self, improvements: PromptImprovements):
        """Print formatted improvements"""

        print(f"\n📝 PROPOSED IMPROVEMENTS")
        print("=" * 70)
        print(f"Summary: {improvements.summary}")
        print(f"Expected Impact: {improvements.expected_impact}")

        print(f"\n🔧 CHANGES ({len(improvements.improvements)}):")
        for i, imp in enumerate(improvements.improvements, 1):
            print(f"\n{i}. {imp.target.upper()}: {imp.name}.{imp.field}")
            print(f"   Rationale: {imp.rationale}")
            print(f"   Change: {len(imp.improved_text)} characters ({'++' if len(imp.improved_text) > len(imp.original_text) else '--'})")


if __name__ == "__main__":
    print("🧪 Prompt Adapter Test")
    print("Note: This module requires analysis results to generate improvements.")
    print("Run full auto_improve_crew.py to see this in action.")
