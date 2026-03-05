---
description: Guidelines for synthesizing raw Scout research into structured analytical content with evidence-based conclusions.
---

# Synthesis Guidelines

## From Raw Research to Analysis

Scout provides raw facts, data points, and sources. Your job is to transform this into analytical content.

## Synthesis Process

### Step 1: Inventory
- Read ALL research files from `research/` folder
- List all unique facts, data points, and sources
- Identify overlapping information between files
- Note any contradictions between sources

### Step 2: Pattern Recognition
- Group related facts across different research files
- Identify trends (e.g., "all modern approaches use X")
- Spot contradictions (source A says X, source B says Y)
- Find gaps (what's missing from the research?)

### Step 3: Structure
- Map facts to document sections based on template
- Ensure each section has supporting evidence
- Place comparison data into tables
- Identify where illustration placeholders should be placed (`<!-- ILLUSTRATION: ... -->`)

### Step 4: Write
- Transform grouped facts into flowing analytical prose
- Each claim backed by at least one source citation
- Draw comparisons explicitly ("Unlike X, approach Y achieves...")
- Add your analytical layer on top of facts

### Step 5: Conclude
- Conclusions must follow from evidence presented in the document
- Include specific recommendations tied to use cases
- Acknowledge limitations and trade-offs

## Citation Style

Inline citations using source URLs:
```markdown
LoRA reduces trainable parameters by 10,000x while maintaining 97% of full fine-tuning performance ([Hu et al., 2021](https://arxiv.org/abs/2106.09685)).
```

## Handling Contradictions

When sources disagree:
1. Present both perspectives with their sources
2. Note the contradiction explicitly
3. If possible, explain why they differ (different contexts, metrics, datasets)
4. Don't take sides without evidence — present the analysis

## Handling Gaps

If Scout research doesn't cover a required section:
1. First, try to synthesize from available data
2. If truly insufficient, request additional Scout research via sub-agent call
3. Never fabricate data or fill with generic text

## Evidence Quality

- Stronger evidence (papers, official docs) supports stronger claims
- Weaker evidence (blogs, forums) supports "some practitioners report..." style claims
- Numerical data requires a source — never estimate without attribution
- Use "approximately" when exact numbers vary across sources
