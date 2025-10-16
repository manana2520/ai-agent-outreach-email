# Auto-Improvement System - Quick Start Guide

## 🚀 What is This?

The Auto-Improvement System is a fully automated testing and optimization framework that continuously improves your sales email crew by:
- Testing with diverse, randomly-generated prospects
- Analyzing failures with LLM-powered root cause analysis
- Adapting agent prompts automatically
- Achieving 95% pass rate without human intervention

## ⚡ Quick Start

### 1. Prerequisites

```bash
# Ensure environment variables are set
export OPENAI_API_KEY="your-key-here"  # Or OPENROUTER_API_KEY
export SERPER_API_KEY="your-key-here"

# Verify crew runs successfully
uv run sales_personalized_email
```

### 2. Test Current Performance

```bash
# Test current crew (no changes made)
python auto_improve_crew.py --test-only --num-prospects 20
```

**Expected Output:**
```
📊 Pass Rate: 75.0% (Target: 95.0%)
Average Quality: 82.3/100
Passed/Failed: 15/5
```

### 3. Run Auto-Improvement

```bash
# Full auto-improvement cycle
python auto_improve_crew.py \
  --max-iterations 10 \
  --target-pass-rate 0.95 \
  --num-prospects 20
```

**What Happens:**
1. Generates 20 diverse test prospects (random industries/roles/selling intents)
2. Runs crew for each, validates quality (85+ score required)
3. Analyzes failures with GPT-4
4. Generates prompt improvements
5. Applies improvements to agents.yaml and tasks.yaml
6. Repeats until 95% pass rate achieved

### 4. Review Results

```bash
# Check final report
cat auto_improvement_report.json

# Review iteration logs
ls improvement_logs/

# Check backed up prompts (original versions)
ls prompt_backups/
```

---

## 📊 Understanding Results

### Pass Criteria

Your email **PASSES** if ALL of these are met:
- ✅ Total score ≥ 85/100
- ✅ Intent compliance ≥ 12/15 (when selling_intent provided)
- ✅ First name capitalized
- ✅ CTA present (score ≥ 3/5)
- ✅ No generic messaging when specific intent provided

### Quality Scoring (100 points)

- **Structure** (35pts): Name capitalization, achievements, industry context, value prop, CTA
- **Personalization** (25pts): LinkedIn confidence, company research, role relevance
- **Message Quality** (25pts): Tone, length, subject line
- **Selling Intent** (15pts): Keyword coverage, specific use case focus

---

## 🔧 Common Commands

### Test Without Changes
```bash
python auto_improve_crew.py --test-only --num-prospects 20
```

### Aggressive Improvement
```bash
python auto_improve_crew.py --max-iterations 15 --target-pass-rate 0.97
```

### Quick Test (Fewer Prospects)
```bash
python auto_improve_crew.py --num-prospects 10 --max-iterations 5
```

### Custom Report Name
```bash
python auto_improve_crew.py --output-report my_improvement_report.json
```

---

## 📈 Typical Performance

### Iteration Breakdown

**Iteration 1** (Initial):
- Pass Rate: 70%
- Failures: Intent compliance, weak CTAs
- Action: Strengthen selling_intent enforcement

**Iteration 2**:
- Pass Rate: 82%
- Failures: LinkedIn research, personalization
- Action: Reduce confidence conservatism

**Iteration 3**:
- Pass Rate: 88%
- Failures: Structure, message quality
- Action: Add explicit format requirements

**Iteration 4**:
- Pass Rate: 95% ✅
- **SUCCESS!**

### Metrics

- **Time per Iteration**: 15-25 minutes (20 prospects)
- **Typical Convergence**: 3-5 iterations
- **Total Runtime**: 1-2 hours
- **Cost**: $20-40 in API calls (GPT-4 + crew executions)

---

## 🛠️ Troubleshooting

### "LLM analysis failed"
**Cause**: API key issue or rate limiting
**Solution**: Check API keys, switch to fallback mode (automatic)

### "Crew execution failed"
**Cause**: Missing dependencies or env variables
**Solution**: Run `uv sync` and verify env variables set

### "No improvement after 3 iterations"
**Cause**: Reached local optimum or systemic issues
**Solution**: System stops automatically. Review failure patterns for architectural issues.

### "Pass rate decreased"
**Cause**: Overfitting or contradictory changes
**Solution**: Restore from `prompt_backups/` and adjust parameters

---

## 📁 File Structure

```
.
├── auto_improve_crew.py                 # Main orchestrator script
├── src/sales_personalized_email/
│   ├── prospect_generator.py            # Random prospect generation
│   ├── test_runner.py                   # Test execution & validation
│   ├── failure_analyzer.py              # LLM failure analysis
│   ├── prompt_adapter.py                # Prompt improvement generation
│   └── email_quality_validator.py       # Quality scoring
├── improvement_logs/                    # Iteration logs
│   ├── iteration_001.json
│   ├── iteration_002.json
│   └── ...
├── prompt_backups/                      # Original prompts
│   └── 20251015_103000/
│       ├── agents.yaml
│       └── tasks.yaml
└── auto_improvement_report.json         # Final report
```

---

## 🎯 What Gets Improved?

### Agent Prompts (agents.yaml)

**Intent Compliance Issues** → Add CRITICAL/MANDATORY sections:
```yaml
CRITICAL SELLING INTENT ENFORCEMENT:
When selling_intent is provided, you MUST use those EXACT keywords.
Subject line MUST contain keywords from selling_intent.
NO generic data platform messaging when specific intent provided.
```

**Personalization Issues** → Reduce conservatism:
```yaml
MANDATORY: You MUST return LinkedIn profiles for unique name+company.
Don't be overly cautious - if profile clearly matches, return it.
```

**CTA Issues** → Add explicit requirements:
```yaml
MANDATORY CTA: Every email MUST end with strong assumptive call-to-action.
Examples: "When's the best time this week for a 15-minute call?"
FORBIDDEN: Weak CTAs like "Would you be open to..."
```

### Task Descriptions (tasks.yaml)

Strengthens requirements, adds examples, clarifies expectations.

---

## ✅ Best Practices

### Before Running

1. ✅ Test crew manually first (`uv run sales_personalized_email`)
2. ✅ Check current pass rate (`--test-only`)
3. ✅ Set API keys (OPENAI_API_KEY, SERPER_API_KEY)
4. ✅ Have ~$40 budget for API calls

### During Execution

1. Monitor iteration logs in real-time
2. Check failure patterns look reasonable
3. Verify improvements make sense

### After Completion

1. Review final report (`auto_improvement_report.json`)
2. Test with known good examples
3. Validate no functionality broken
4. Commit improved prompts
5. Document changes in CHANGELOG

---

## 🚨 Important Notes

- **Backup Created**: Original prompts automatically backed up to `prompt_backups/`
- **Restore Anytime**: Copy files from backup to restore original prompts
- **Early Stopping**: System stops if no improvement for 3 iterations
- **Max Iterations**: Hard limit prevents runaway costs
- **Test Data**: New random prospects each iteration (no overfitting)

---

## 📚 Additional Documentation

- **`AUTO_IMPROVEMENT_SPEC.md`**: Full system specification
- **`AUTO_IMPROVEMENT_IMPLEMENTATION_PLAN.md`**: Technical implementation details
- **`CLAUDE.md`**: Project overview and commands
- **`docs/CHANGELOG.md`**: Track prompt changes

---

## 🎉 Success Example

```json
{
  "success": true,
  "iterations": 4,
  "initial_pass_rate": 0.70,
  "final_pass_rate": 0.95,
  "improvement": 0.25,
  "final_avg_quality": 91.2,
  "message": "Successfully achieved 95.0% pass rate in 4 iterations"
}
```

**Result**: Your crew now consistently generates high-quality, personalized emails that:
- Score 85+ on quality rubric
- Use specific selling_intent keywords
- Include strong CTAs
- Maintain proper structure
- Are highly personalized

---

**Questions?** Check `AUTO_IMPROVEMENT_SPEC.md` for full details or review iteration logs for specific failure patterns.
