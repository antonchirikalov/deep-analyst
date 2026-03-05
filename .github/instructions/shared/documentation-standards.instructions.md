---
description: General document formatting rules and standards for all Deep Analyst output documents.
---

# Documentation Standards

## Markdown Formatting

- Use ATX-style headings (`#`, `##`, `###`)
- One blank line before and after headings
- One blank line before and after code blocks
- One blank line before and after tables
- Lists: use `-` for unordered, `1.` for ordered
- Bold for emphasis: `**important**`
- Inline code for technical terms: `` `model_name` ``

## Heading Hierarchy

```
# Document Title (H1) — one per document
## Major Section (H2)
### Subsection (H3)
#### Detail (H4) — use sparingly
```

- Never skip levels (no H1 → H3)
- Section numbers required: `## 1. Introduction`, `## 2. Background`
- Subsection numbers: `### 2.1 [Name]`, `### 2.2 [Name]`

## Tables

- Use tables for structured comparisons (3+ items × 3+ attributes)
- Include header row with bold or clear labels
- Align columns for readability
- Keep cell content concise (1–2 lines max)

## Source Citations

Inline citation format:
```markdown
LoRA achieves 97% of full fine-tuning performance ([Hu et al., 2021](https://arxiv.org/abs/2106.09685)).
```

Sources section format:
```markdown
## Sources
- [Official LoRA Paper](https://arxiv.org/abs/2106.09685) — Original LoRA method description, parameter reduction analysis
- [PyTorch Documentation](https://pytorch.org/docs/stable/) — Implementation reference for training loops
```

## Language

- English by default (match user query language)
- Technical terms explained on first use
- Active voice preferred
- Consistent terminology throughout document
- No informal language or slang

## Version Tracking

Draft files use version numbering: `v1.md`, `v2.md`, `v3.md`
- v1 = initial synthesis from Scout research
- v2 = post-Critic revision
- v3 = second revision (if needed)
- FINAL_REPORT.md = copy of approved version
