# Auto-Improving Personalized Sales Email Agent Specification

## 1. Quality Scoring Rubric (100-Point System)

### Structure Compliance (40 points)
- **First Name Capitalized** (5 points): Must start with proper capitalization
- **Achievement Recognition** (10 points): Specific achievement mentioned (8-10) or generic pleasing (6-7)
- **Industry Context** (10 points): Keboola customer use case from similar industry
- **Value Proposition** (10 points): How Keboola can help prospect's specific industry
- **Call-to-Action** (5 points): Clear meeting request (demo or consulting)

### Personalization Quality (30 points)
- **LinkedIn Confidence** (15 points): 
  - High confidence (90-100%): 15 points
  - Medium confidence (70-89%): 12 points  
  - Low confidence (<70%): 8 points
- **Company Research Depth** (10 points): Company achievements, recent news, industry context
- **Role Relevance** (5 points): Technical messaging for technical roles, business for business

### Message Quality (30 points)
- **Tone & Flow** (15 points): Professional, conversational, smooth transitions
- **Length & Crispness** (10 points): 4-6 paragraphs, 120-180 words total
- **Subject Line Impact** (5 points): Compelling, personalized, action-oriented

## 2. Email Structure Template

### High Confidence Template (LinkedIn confidence >85%)
```
Subject: [Specific Achievement] - How [Similar Company] Cut Data Costs 50%

Hi [FirstName],

Congratulations on [specific achievement from LinkedIn research]! [Brief context about why this achievement matters in their industry].

We recently helped [Similar Industry Company] achieve [specific metric/outcome] using our data platform. [Brief 1-sentence description of the use case].

Given your role at [Company] and focus on [specific area], I believe we could help you achieve similar results in [specific industry challenge/area].

Would you be open to a brief 15-minute call to explore how this might apply to your situation?

Best regards,
[Name]
```

### Low Confidence Template (LinkedIn confidence <70%)
```
Subject: How [Industry] Leaders Are Cutting Data Tool Costs by 50%

Hi [FirstName],

I noticed [Company] is doing impressive work in [industry]. Companies like yours are often looking for ways to streamline their data operations.

We recently helped [Similar Industry Company] achieve [specific metric] by consolidating their data stack. [Brief description of industry-relevant use case].

Given [Company]'s position in [industry], I believe there could be similar opportunities to optimize your data operations.

Are you free Tuesday or Wednesday for a 15-minute call?

Best regards,
[Name]
```

## 3. Selling Intent Dynamic Handling

### When Selling Intent Provided
- Email MUST contain ALL keywords from the selling intent
- Subject line MUST include at least one keyword
- Body must focus EXCLUSIVELY on that use case
- Example: "coffee machine" → discuss coffee operations, facilities management, predictive maintenance
- FORBIDDEN: Generic data platform messaging

### When NO Selling Intent Provided  
- Use general Keboola benefits for their industry
- Focus on industry-specific use cases from research
- Reference relevant customer success stories

## 4. Confidence Scoring System

### LinkedIn Profile Validation (0-100%)
- **Exact name + company match + recent activity**: 95-100%
- **Exact name + company match + profile accessible**: 85-94%
- **Name match + company context + some uncertainty**: 70-84%
- **Common name + partial company match**: 50-69%
- **No clear match found**: 0-49%

### Title Discovery Confidence (0-100%)
- **Explicitly stated on verified LinkedIn**: 95-100%
- **Stated on company website or press release**: 85-94%
- **Inferred from multiple consistent sources**: 70-84%
- **Partial or outdated information**: 50-69%
- **No title information found**: 0-49%

### Country/Location Confidence (0-100%)
- **LinkedIn location + company office match**: 95-100%
- **LinkedIn location stated clearly**: 85-94%
- **Company headquarters/office location**: 70-84%
- **General region inferred**: 50-69%
- **No location information**: 0-49%

## 4. Industry-Specific Keboola Use Cases

### Financial Services
- **Customer**: Home Credit (consumer finance)
- **Achievement**: 70% reduction in FP&A reporting time
- **Technical**: Real-time risk assessment, automated compliance reporting
- **Business**: Faster decision-making, reduced operational costs

### Retail/E-commerce
- **Customer**: Rohlik (online grocery), BRIX (fashion)
- **Achievement**: 80% reduction in manual data processing
- **Technical**: Inventory optimization, customer segmentation automation
- **Business**: Improved margins, better customer experience

### Logistics/Supply Chain
- **Customer**: P3 Logistic Parks
- **Achievement**: Unified data across 8 countries
- **Technical**: IoT data integration, predictive maintenance
- **Business**: Operational visibility, cost optimization

### Manufacturing
- **Achievement**: 50% reduction in data tool costs
- **Technical**: Production line monitoring, quality control automation
- **Business**: Improved efficiency, reduced downtime

### Technology/SaaS
- **Achievement**: Launch analytics projects in days vs months
- **Technical**: Customer usage analytics, product optimization
- **Business**: Faster time-to-market, data-driven decisions

## 5. Auto-Improvement Loop Algorithm

### Quality Assessment Function
```python
def calculate_email_quality_score(email_content, research_data, inputs):
    score = 0
    
    # Structure Compliance (40 points)
    score += check_first_name_capitalization(email_content, inputs) # 5 points
    score += check_achievement_recognition(email_content, research_data) # 10 points
    score += check_industry_context(email_content, inputs) # 10 points
    score += check_value_proposition(email_content, inputs) # 10 points
    score += check_call_to_action(email_content) # 5 points
    
    # Personalization Quality (30 points)
    score += calculate_linkedin_confidence_points(research_data) # 15 points
    score += check_company_research_depth(email_content, research_data) # 10 points
    score += check_role_relevance(email_content, inputs) # 5 points
    
    # Message Quality (30 points)
    score += check_tone_and_flow(email_content) # 15 points
    score += check_length_and_crispness(email_content) # 10 points
    score += check_subject_line(email_content, inputs) # 5 points
    
    return score
```

### Re-generation Triggers
- **Score < 70**: Immediate regeneration with enhanced prompts
- **Score 70-84**: Single optimization attempt
- **Score ≥ 85**: Accept and log
- **Maximum 3 regeneration attempts per email**

### Prompt Optimization Rules
1. **Low personalization scores**: Enhance LinkedIn research prompts
2. **Poor structure scores**: Strengthen email format instructions  
3. **Weak industry context**: Improve use case research prompts
4. **Generic messaging**: Enhance achievement recognition prompts

## 6. Agent Prompt Modifications

### LinkedIn Research Agent Enhancement
```
Your confidence assessment must be numeric (0-100%) based on:
- Exact name/company match + recent activity: 95-100%
- Exact name/company match + accessible profile: 85-94%
- Name match + company context + minor uncertainty: 70-84%
- Common name + partial match: 50-69%
- No clear match: 0-49%

CRITICAL: Return numeric confidence scores for LinkedIn profile, title, and country.
```

### Achievement Recognition Agent Enhancement
```
PRIORITY ORDER for achievements:
1. Recent promotions or role changes (within 6 months)
2. Company awards, recognitions, certifications
3. Published articles, speaking engagements
4. Company milestones, funding rounds, expansions

When LinkedIn confidence < 70%, focus on COMPANY achievements instead of personal ones.
Provide specific, measurable achievements with context.
```

### Email Copywriter Agent Enhancement
```
MANDATORY EMAIL STRUCTURE:
Paragraph 1: Hi [FirstName], [Achievement recognition - specific if confidence >70%, generic if <70%]
Paragraph 2: We recently helped [Similar Industry Company] achieve [specific metric]. [Use case description].
Paragraph 3: Given your role at [Company], I believe we could help you [specific benefit].
Paragraph 4: Would you be open to a brief 15-minute call to explore this?
Paragraph 5: Best regards, [Name]

WORD COUNT: 120-180 words total
CONFIDENCE HANDLING: Use specific achievements when LinkedIn confidence >70%, company-focused when <70%
```

## 7. Implementation Steps

### Week 1: Foundation & Scoring System
1. Implement `EmailQualityValidator` class
2. Add confidence scoring to all agents
3. Create email structure validation
4. Build basic regeneration logic

### Week 2: Auto-Improvement Loop
1. Implement quality assessment algorithm
2. Add regeneration triggers and limits
3. Create prompt optimization system
4. Build performance tracking

### Week 3: Industry Specialization
1. Add Keboola use case database
2. Implement role-based messaging (technical vs business)
3. Enhanced industry context prompts
4. Customer story integration

### Week 4: Production Deployment
1. Integration testing with sample prospects
2. Performance validation against quality metrics
3. Monitoring and alerting setup
4. Documentation and training

## 8. Success Metrics

### Quality KPIs
- **Average Email Quality Score**: ≥85/100
- **Regeneration Rate**: <20% of emails require regeneration
- **Confidence Accuracy**: LinkedIn validation accuracy >90%
- **Structure Compliance**: 100% of emails follow template

### Performance KPIs
- **Processing Time**: <3 minutes per email (including regenerations)
- **API Success Rate**: >99% successful completions
- **Error Rate**: <1% system errors

### Business KPIs
- **Response Rate**: Track email response rates (target baseline +20%)
- **Meeting Booking Rate**: Track successful meeting bookings
- **Quality Consistency**: Standard deviation of quality scores <10

## 9. Testing Framework

### Test Scenarios
1. **High-confidence LinkedIn profile** (Milan Kulhanek, Deloitte)
2. **Medium-confidence profile** (Common name, clear company)
3. **Low-confidence profile** (No LinkedIn found)
4. **Technical role** (CTO, Data Engineer)
5. **Business role** (VP Sales, CMO)
6. **Various industries** (Finance, Retail, Manufacturing)
7. **No hardcoding validation** - Verify no hardcoded examples (coffee, education, etc.)
   - Test with diverse selling_intents to ensure dynamic handling
   - Verify agent doesn't default to specific hardcoded examples
   - Ensure customer examples are researched, not hardcoded

### Expected Outcomes
- High confidence: Specific achievement recognition, score >85
- Low confidence: Generic but professional messaging, score >70
- Technical role: Technical use cases and terminology
- Business role: Business value and ROI focus
- No hardcoding: Dynamic content generation based on actual inputs
  - No default to "education" or "coffee" when unrelated to prospect
  - Selling intent keywords properly reflected in output
  - Customer examples dynamically researched, not hardcoded

## 10. Monitoring & Maintenance

### Automated Monitoring
- Quality score distribution tracking
- Regeneration pattern analysis
- Confidence accuracy validation
- Performance metric dashboards

### Continuous Improvement
- Monthly quality score analysis
- Prompt effectiveness review
- Industry use case updates
- Customer feedback integration

This specification ensures the email agent will automatically generate high-quality, personalized sales emails that meet all requirements while continuously improving its performance through automated quality assessment and optimization.

---

## 11. Automated Crew Improvement System

### Overview

The automated crew improvement system continuously tests, analyzes, and adapts agent prompts to achieve and maintain a 95% pass rate. The system operates autonomously without human intervention, using LLM-powered analysis to identify failure patterns and generate targeted prompt improvements.

### System Architecture

```
ORCHESTRATOR → PROSPECT GENERATOR → TEST RUNNER → FAILURE ANALYZER → PROMPT ADAPTER → YAML UPDATER
      ↑                                                                                        ↓
      └────────────────────────────────────────────────────────────────────────────────────────┘
```

**Components:**
1. **Prospect Generator**: Creates diverse test prospects (random industries, roles, geographies, selling intents)
2. **Test Runner**: Executes crew and validates outputs against quality criteria
3. **Failure Analyzer**: LLM-powered root cause analysis of failures
4. **Prompt Adapter**: LLM-generated prompt improvements
5. **Orchestrator**: Coordinates iteration cycles until target achieved

### Quality Criteria for 95% Pass Rate

A test **PASSES** if ALL criteria met:
- Total quality score ≥ 85/100
- Intent compliance ≥ 12/15 (when selling_intent provided)
- First name properly capitalized
- CTA present (score ≥ 3/5)
- No generic messaging when specific intent provided

### Usage

```bash
# Full auto-improvement cycle
python auto_improve_crew.py --max-iterations 10 --target-pass-rate 0.95 --num-prospects 20

# Test only (no adaptation)
python auto_improve_crew.py --test-only --num-prospects 20

# Custom configuration
python auto_improve_crew.py --max-iterations 15 --target-pass-rate 0.97 --num-prospects 30
```

**Parameters:**
- `--max-iterations`: Maximum improvement cycles (default: 10)
- `--target-pass-rate`: Target pass rate 0-1 (default: 0.95)
- `--num-prospects`: Prospects per iteration (default: 20)
- `--output-report`: JSON report file
- `--test-only`: Run tests without adapting
- `--no-backup`: Skip prompt backup

### Iteration Cycle

Each iteration follows five automated steps:

1. **Generate Prospects**: 20 diverse prospects with random industries, roles, and selling intents
2. **Run Tests**: Execute crew for each prospect, validate against quality criteria
3. **Analyze Failures**: LLM identifies failure patterns and root causes
4. **Generate Improvements**: LLM creates targeted prompt enhancements
5. **Apply Improvements**: Update agents.yaml and tasks.yaml

### Convergence

**Success**: Pass rate ≥ 95%
**Early Stopping**: No improvement for 3 iterations
**Typical Performance**: 70% → 95% pass rate in 3-5 iterations

### Failure Pattern Detection

Five primary failure patterns:

1. **Intent Compliance** (CRITICAL): Using generic messaging instead of specific selling_intent
2. **Personalization**: Low LinkedIn confidence or insufficient research
3. **Structure**: Missing required email elements
4. **Message Quality**: Poor tone, length, or subject line
5. **CTA**: Missing or weak call-to-action

### Prompt Adaptation Strategies

**Intent Failures** → Add CRITICAL/MANDATORY sections enforcing selling_intent keywords
**Personalization Failures** → Reduce LinkedIn confidence conservatism
**CTA Failures** → Add explicit CTA requirements with examples
**Structure Failures** → Strengthen email format instructions

### Output Artifacts

- **Prompt Backups**: `prompt_backups/YYYYMMDD_HHMMSS/`
- **Iteration Logs**: `improvement_logs/iteration_001.json`
- **Final Report**: `auto_improvement_report.json`

### Performance Metrics

- **Iteration Time**: 15-25 minutes (20 prospects)
- **Total Runtime**: 1-2 hours (typical convergence)
- **Convergence**: 3-5 iterations average
- **Cost**: ~$20-40 in API calls

### Best Practices

**Before Running:**
1. Set OPENAI_API_KEY or OPENROUTER_API_KEY
2. Set SERPER_API_KEY
3. Test crew runs successfully manually
4. Review current pass rate with `--test-only`

**After Completion:**
1. Review final report
2. Validate improvements with known examples
3. Commit improved prompts
4. Document changes in changelog

See `AUTO_IMPROVEMENT_IMPLEMENTATION_PLAN.md` for full technical details.