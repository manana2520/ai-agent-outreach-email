#!/usr/bin/env python3
"""
Auto-Improvement Orchestrator for Sales Email Crew

Automatically tests, analyzes, and improves crew prompts until achieving 95% pass rate.
Uses LLM-powered analysis to adapt agent and task prompts based on real failures.

Usage:
    python auto_improve_crew.py --max-iterations 10 --target-pass-rate 0.95 --num-prospects 20
    python auto_improve_crew.py --test-only --num-prospects 20
"""

import argparse
import json
import os
import shutil
import yaml
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

from src.sales_personalized_email.prospect_generator import RandomProspectGenerator
from src.sales_personalized_email.test_runner import CrewTestRunner
from src.sales_personalized_email.failure_analyzer import FailureAnalyzer
from src.sales_personalized_email.prompt_adapter import PromptAdapter


@dataclass
class ImprovementReport:
    """Final improvement cycle report"""
    success: bool
    iterations: int
    final_pass_rate: float
    target_pass_rate: float
    initial_pass_rate: float
    improvement: float
    final_avg_quality: float
    total_tests_run: int
    timestamp: str
    iteration_history: list
    message: str = ""


class AutoImprovementOrchestrator:
    """
    Main orchestrator for automated crew improvement.

    Coordinates:
    1. Prospect generation
    2. Test execution
    3. Failure analysis
    4. Prompt adaptation
    5. Iteration management
    """

    def __init__(
        self,
        max_iterations: int = 10,
        target_pass_rate: float = 0.95,
        num_test_prospects: int = 20,
        agents_yaml_path: str = "src/sales_personalized_email/config/agents.yaml",
        tasks_yaml_path: str = "src/sales_personalized_email/config/tasks.yaml",
        backup_prompts: bool = True
    ):
        """
        Initialize orchestrator.

        Args:
            max_iterations: Maximum improvement iterations
            target_pass_rate: Target pass rate (default: 0.95)
            num_test_prospects: Prospects per test run
            agents_yaml_path: Path to agents.yaml
            tasks_yaml_path: Path to tasks.yaml
            backup_prompts: Create backup of original prompts
        """
        self.max_iterations = max_iterations
        self.target_pass_rate = target_pass_rate
        self.num_test_prospects = num_test_prospects
        self.agents_yaml_path = agents_yaml_path
        self.tasks_yaml_path = tasks_yaml_path

        # Initialize components
        self.prospect_generator = RandomProspectGenerator()
        self.test_runner = CrewTestRunner()
        self.failure_analyzer = FailureAnalyzer()
        self.prompt_adapter = PromptAdapter()

        # Backup original prompts
        if backup_prompts:
            self._backup_prompts()

        # Create logs directory
        os.makedirs('improvement_logs', exist_ok=True)

        # Iteration history
        self.iteration_history = []

    def run_improvement_cycle(self) -> ImprovementReport:
        """
        Run complete improvement cycle.

        Returns:
            ImprovementReport with results and history
        """

        print("\n" + "="*80)
        print("🚀 AUTO-IMPROVEMENT CYCLE STARTING")
        print("="*80)
        print(f"Max Iterations: {self.max_iterations}")
        print(f"Target Pass Rate: {self.target_pass_rate*100:.0f}%")
        print(f"Prospects per Iteration: {self.num_test_prospects}")
        print(f"Quality Threshold: 85/100")
        print("="*80)

        initial_pass_rate = None
        iteration = 0

        # Early stopping: no improvement for 3 iterations
        no_improvement_count = 0
        best_pass_rate = 0.0

        while iteration < self.max_iterations:
            iteration += 1

            print(f"\n{'#'*80}")
            print(f"# ITERATION {iteration}/{self.max_iterations}")
            print(f"{'#'*80}")

            # 1. Generate test prospects
            print(f"\n[Step 1/5] Generating {self.num_test_prospects} diverse test prospects...")
            prospects = self.prospect_generator.generate_test_prospects(
                num_prospects=self.num_test_prospects,
                ensure_diversity=True
            )

            # 2. Run test suite
            print(f"\n[Step 2/5] Running test suite...")
            results = self.test_runner.run_test_suite(
                prospects=prospects,
                target_pass_rate=self.target_pass_rate
            )

            pass_rate = results.pass_rate
            avg_quality = results.avg_quality_score

            # Save initial pass rate
            if initial_pass_rate is None:
                initial_pass_rate = pass_rate

            # Log iteration
            iteration_log = {
                'iteration': iteration,
                'pass_rate': pass_rate,
                'avg_quality': avg_quality,
                'passed': results.passed_tests,
                'failed': results.failed_tests,
                'failure_patterns': results.failure_patterns,
                'timestamp': datetime.now().isoformat()
            }
            self.iteration_history.append(iteration_log)

            print(f"\n📊 ITERATION {iteration} RESULTS:")
            print(f"   Pass Rate: {pass_rate*100:.1f}% (Target: {self.target_pass_rate*100:.0f}%)")
            print(f"   Average Quality: {avg_quality:.1f}/100")
            print(f"   Passed/Failed: {results.passed_tests}/{results.failed_tests}")

            # 3. Check if target achieved
            if pass_rate >= self.target_pass_rate:
                print(f"\n🎉 SUCCESS! Achieved {pass_rate*100:.1f}% pass rate!")
                return self._create_success_report(
                    iteration, pass_rate, initial_pass_rate, avg_quality,
                    iteration * self.num_test_prospects
                )

            # Early stopping check
            if pass_rate <= best_pass_rate:
                no_improvement_count += 1
                print(f"\n⚠️  No improvement for {no_improvement_count} iteration(s)")
                if no_improvement_count >= 3:
                    print(f"\n🛑 Early stopping: No improvement for 3 iterations")
                    return self._create_failure_report(
                        iteration, pass_rate, initial_pass_rate, avg_quality,
                        iteration * self.num_test_prospects,
                        "Early stopping: No improvement for 3 iterations"
                    )
            else:
                best_pass_rate = pass_rate
                no_improvement_count = 0

            # 4. Analyze failures
            print(f"\n[Step 3/5] Analyzing {results.num_failures} failures...")

            # Load current prompts
            with open(self.agents_yaml_path, 'r') as f:
                agents_yaml = f.read()
            with open(self.tasks_yaml_path, 'r') as f:
                tasks_yaml = f.read()

            analysis = self.failure_analyzer.analyze_failures(
                test_results=results,
                current_agents_yaml=agents_yaml,
                current_tasks_yaml=tasks_yaml
            )

            # Add analysis to iteration log
            iteration_log['analysis'] = {
                'failure_patterns': [asdict(p) for p in analysis.failure_patterns],
                'priority_fixes': analysis.priority_fixes,
                'summary': analysis.summary
            }

            # 5. Generate prompt improvements
            print(f"\n[Step 4/5] Generating prompt improvements...")

            with open(self.agents_yaml_path, 'r') as f:
                current_agents = yaml.safe_load(f)
            with open(self.tasks_yaml_path, 'r') as f:
                current_tasks = yaml.safe_load(f)

            improvements = self.prompt_adapter.adapt_prompts(
                analysis=analysis,
                current_agents=current_agents,
                current_tasks=current_tasks,
                failure_examples=results.failures[:5]
            )

            # Add improvements to iteration log
            iteration_log['improvements'] = {
                'num_improvements': len(improvements.improvements),
                'summary': improvements.summary,
                'expected_impact': improvements.expected_impact
            }

            # 6. Apply improvements
            print(f"\n[Step 5/5] Applying improvements...")
            self.prompt_adapter.apply_improvements(
                improvements=improvements,
                agents_yaml_path=self.agents_yaml_path,
                tasks_yaml_path=self.tasks_yaml_path
            )

            # Save iteration log
            self._save_iteration_log(iteration, iteration_log)

            print(f"\n✅ Iteration {iteration} complete")
            print(f"   Pass Rate Improvement: {initial_pass_rate*100:.1f}% → {pass_rate*100:.1f}% (+{(pass_rate-initial_pass_rate)*100:.1f}%)")

        # Max iterations reached without success
        return self._create_failure_report(
            self.max_iterations, pass_rate, initial_pass_rate, avg_quality,
            self.max_iterations * self.num_test_prospects,
            f"Max iterations ({self.max_iterations}) reached without achieving target"
        )

    def test_only(self) -> ImprovementReport:
        """
        Run test suite without adapting prompts.

        Returns:
            ImprovementReport with test results only
        """

        print("\n" + "="*80)
        print("🧪 TEST-ONLY MODE")
        print("="*80)
        print(f"Testing current crew with {self.num_test_prospects} prospects")
        print("="*80)

        # Generate prospects
        print(f"\nGenerating {self.num_test_prospects} test prospects...")
        prospects = self.prospect_generator.generate_test_prospects(
            num_prospects=self.num_test_prospects,
            ensure_diversity=True
        )

        # Run tests
        print(f"\nRunning test suite...")
        results = self.test_runner.run_test_suite(
            prospects=prospects,
            target_pass_rate=self.target_pass_rate
        )

        # Create report
        return ImprovementReport(
            success=results.pass_rate >= self.target_pass_rate,
            iterations=1,
            final_pass_rate=results.pass_rate,
            target_pass_rate=self.target_pass_rate,
            initial_pass_rate=results.pass_rate,
            improvement=0.0,
            final_avg_quality=results.avg_quality_score,
            total_tests_run=self.num_test_prospects,
            timestamp=datetime.now().isoformat(),
            iteration_history=[],
            message="Test-only mode - no improvements applied"
        )

    def _backup_prompts(self):
        """Create backup of original prompts"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'prompt_backups/{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)

        shutil.copy(self.agents_yaml_path, f'{backup_dir}/agents.yaml')
        shutil.copy(self.tasks_yaml_path, f'{backup_dir}/tasks.yaml')

        print(f"✅ Backed up prompts to {backup_dir}")

    def _save_iteration_log(self, iteration: int, log: dict):
        """Save iteration log to file"""
        log_file = f'improvement_logs/iteration_{iteration:03d}.json'
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)
        print(f"   Saved log to {log_file}")

    def _create_success_report(
        self,
        iterations: int,
        final_pass_rate: float,
        initial_pass_rate: float,
        final_avg_quality: float,
        total_tests: int
    ) -> ImprovementReport:
        """Create success report"""
        return ImprovementReport(
            success=True,
            iterations=iterations,
            final_pass_rate=final_pass_rate,
            target_pass_rate=self.target_pass_rate,
            initial_pass_rate=initial_pass_rate,
            improvement=final_pass_rate - initial_pass_rate,
            final_avg_quality=final_avg_quality,
            total_tests_run=total_tests,
            timestamp=datetime.now().isoformat(),
            iteration_history=self.iteration_history,
            message=f"Successfully achieved {final_pass_rate*100:.1f}% pass rate in {iterations} iterations"
        )

    def _create_failure_report(
        self,
        iterations: int,
        final_pass_rate: float,
        initial_pass_rate: float,
        final_avg_quality: float,
        total_tests: int,
        message: str
    ) -> ImprovementReport:
        """Create failure report"""
        return ImprovementReport(
            success=False,
            iterations=iterations,
            final_pass_rate=final_pass_rate,
            target_pass_rate=self.target_pass_rate,
            initial_pass_rate=initial_pass_rate or 0.0,
            improvement=final_pass_rate - (initial_pass_rate or 0.0),
            final_avg_quality=final_avg_quality,
            total_tests_run=total_tests,
            timestamp=datetime.now().isoformat(),
            iteration_history=self.iteration_history,
            message=message
        )


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='Auto-improve crew prompts based on test failures'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum improvement iterations (default: 10)'
    )

    parser.add_argument(
        '--target-pass-rate',
        type=float,
        default=0.95,
        help='Target pass rate (default: 0.95)'
    )

    parser.add_argument(
        '--num-prospects',
        type=int,
        default=20,
        help='Number of test prospects per iteration (default: 20)'
    )

    parser.add_argument(
        '--output-report',
        type=str,
        default='auto_improvement_report.json',
        help='Output report file (default: auto_improvement_report.json)'
    )

    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Run tests without adapting prompts'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup of original prompts'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = AutoImprovementOrchestrator(
        max_iterations=args.max_iterations,
        target_pass_rate=args.target_pass_rate,
        num_test_prospects=args.num_prospects,
        backup_prompts=not args.no_backup
    )

    # Run
    if args.test_only:
        report = orchestrator.test_only()
    else:
        report = orchestrator.run_improvement_cycle()

    # Save report
    with open(args.output_report, 'w') as f:
        json.dump(asdict(report), f, indent=2)

    # Print final report
    print("\n" + "="*80)
    print("📊 FINAL REPORT")
    print("="*80)
    print(f"Success: {'✅ YES' if report.success else '❌ NO'}")
    print(f"Iterations: {report.iterations}")
    print(f"Initial Pass Rate: {report.initial_pass_rate*100:.1f}%")
    print(f"Final Pass Rate: {report.final_pass_rate*100:.1f}%")
    print(f"Improvement: {report.improvement*100:+.1f}%")
    print(f"Final Avg Quality: {report.final_avg_quality:.1f}/100")
    print(f"Total Tests Run: {report.total_tests_run}")
    print(f"Message: {report.message}")
    print(f"\nReport saved to: {args.output_report}")
    print("="*80)

    # Exit code
    exit(0 if report.success else 1)


if __name__ == "__main__":
    main()
