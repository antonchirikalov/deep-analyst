---
description: Document type templates for Analyst — structure templates for comparative analysis, technology overview, state of the art, and research report.
---

# Document Templates

## 1. Comparative Analysis

**Use when:** Comparing 2+ technologies, approaches, tools, or methods.

```markdown
# Comparative Analysis: [Topic]

## 1. Introduction
## 2. Comparison Methodology
## 3. Participant Overview
### 3.1 [Technology A]
### 3.2 [Technology B]
### 3.N [Technology N]
## 4. Comparison Table
## 5. Detailed Comparison by Criteria
### 5.1 [Criterion 1]
### 5.2 [Criterion 2]
## 6. Use Cases
## 7. Conclusions and Recommendations
## 8. Sources
```

**Required Illustrations (Analyst leaves `<!-- ILLUSTRATION -->` placeholders):** Architecture diagram per approach + Visual comparison infographic + Decision flowchart "when to choose what"

## 2. Technology Overview

**Use when:** Explaining a single technology, framework, or concept.

```markdown
# Overview: [Technology]

## 1. Introduction and Context
## 2. Historical Background
## 3. Key Concepts
## 4. Architecture / How It Works
## 5. Current Implementations
## 6. Advantages and Limitations
## 7. Practical Applications
## 8. Development Prospects
## 9. Conclusions
## 10. Sources
```

**Required Illustrations (Analyst leaves `<!-- ILLUSTRATION -->` placeholders):** Architecture diagram + Dataflow pipeline + Sequence/flow diagram

## 3. State of the Art

**Use when:** Surveying current leading methods in a field.

```markdown
# State of the Art: [Domain]

## 1. Introduction
## 2. Evolution of Approaches (Timeline)
## 3. Current Leading Methods
### 3.1 [Method/Approach 1]
### 3.2 [Method/Approach 2]
## 4. Benchmarks and Metrics
## 5. Open Problems
## 6. Promising Directions
## 7. Conclusions
## 8. Sources
```

**Required Illustrations (Analyst leaves `<!-- ILLUSTRATION -->` placeholders):** Visual evolution timeline + Methods taxonomy map + Mindmap of current approaches

## 4. Research Report

**Use when:** Investigating a specific question or hypothesis.

```markdown
# Research: [Topic]

## 1. Abstract
## 2. Problem Statement
## 3. Literature Review
## 4. Approach Analysis
### 4.1 [Approach 1]
### 4.2 [Approach 2]
## 5. Results and Data
## 6. Discussion
## 7. Research Limitations
## 8. Conclusion
## 9. Sources
```

**Required Illustrations (Analyst leaves `<!-- ILLUSTRATION -->` placeholders):** Methodology visualization + Results infographic + Comparison flowchart

## Template Rules

- Use the template as a starting point — adjust sections based on actual content
- Every document starts with an Executive Summary (5–7 sentences) before Section 1
- Every document ends with a Sources section with brief URL descriptions
- Section numbering is required for cross-referencing
- **ALL visuals** = Analyst inserts `<!-- ILLUSTRATION: type=..., section=..., description="..." -->` placeholders — the Illustrator generates PaperBanana PNGs (see illustration-guidelines for format and rules)
- Every document MUST have **3–5 illustration placeholders**
- NO inline code-based diagrams — all visualizations are PaperBanana PNG illustrations
