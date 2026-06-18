# OpenAI Prompt

This document describes the sanitized prompt structure used in the Derver diagnostic survey workflow. The original prompt was executed inside a Make scenario after a respondent completed a Tally form. Dynamic values are represented here as generic placeholders.

## Model Configuration

| Setting | Value |
| --- | --- |
| Model | `o3-mini` |
| Temperature | `0.7` |
| Top P | `1` |
| Response format | `text` |
| Reasoning effort | `medium` |

## System Message

```text
You are a business strategy and data science expert tasked with analyzing the responses to a business diagnostic survey.
Write the body of an extended feedback email to be sent to the survey respondent. Analyze the survey responses to extract key issues, hidden tensions, and weak signals.
Keep the tone professional but accessible. Use {{company_name}} to clearly identify the company.
The assessment will be used to support the creation of a roadmap of interventions and pilot projects designed to foster AI adoption, innovation, and data analytics maturity.
```

## User Message

```text
You have received the responses to a survey completed by a business owner. Based on these responses, prepare an extended feedback message that will follow the core results already shared via email.

The feedback focuses on two key dimensions:
1. Strategic tension: the degree of internal complexity and friction between ambitious objectives and organizational or technical blockers.
2. Epistemic maturity: the company's ability to produce, share, and use reliable knowledge to make decisions.

Here is the core feedback already generated:

Strategic tension feedback:
{{core_feedback_strategic_tension}}

Epistemic maturity feedback:
{{core_feedback_epistemic_maturity}}

Based on these elements, write two to three paragraphs that expand the feedback, also considering the following contextual information:

- Additional notes from the owner regarding strategic challenges:
{{strategic_challenges_notes}}

- Additional notes about blockers:
{{blockers_notes}}

- Area-specific criticalities described by the owner:
{{area_criticalities}}

- Recurring decision questions the owner needs to answer:
{{recurring_decision_questions}}

- Current strategic orientation toward business analytics, data science, and artificial intelligence:
{{analytics_ai_strategy_orientation}}

- Perceived risks or concerns around analytics and AI initiatives:
{{analytics_ai_risks}}

- Structured company profile:
{{company_profile}}

Write in Italian using a professional tone.
Do not repeat the original answers or the main feedback. Instead, infer implications, highlight tensions, suggest unexpected links, and identify weak signals that may be worth exploring.
The goal is to offer a thoughtful and stimulating reflection that can support the next step of the diagnostic process, namely a follow-up interview with area leaders.
Keep the feedback relatively abstract.
Do not include introductions or closing statements, as these will be added separately in the email body.
```

## Prompt Inputs

| Placeholder | Source |
| --- | --- |
| `{{company_name}}` | Company name from the Tally response. |
| `{{core_feedback_strategic_tension}}` | Deterministic score feedback for strategic tension. |
| `{{core_feedback_epistemic_maturity}}` | Deterministic score feedback for epistemic maturity. |
| `{{strategic_challenges_notes}}` | Optional free-text notes about strategic challenges. |
| `{{blockers_notes}}` | Optional free-text notes about blockers. |
| `{{area_criticalities}}` | Area-specific criticalities collected in the survey. |
| `{{recurring_decision_questions}}` | Questions the respondent regularly needs to answer to make decisions. |
| `{{analytics_ai_strategy_orientation}}` | Survey answer about analytics, data science, and AI strategy. |
| `{{analytics_ai_risks}}` | Selected or described risks around analytics and AI initiatives. |
| `{{company_profile}}` | Company profile fields such as location, size, sector, market, and production strategy. |

## Output Contract

- Language: Italian.
- Length: two to three paragraphs.
- Tone: professional, accessible, reflective.
- Exclusions: no greeting, no closing, no repetition of the deterministic feedback.
- Purpose: expand the automated score feedback and prepare the ground for a follow-up diagnostic interview.

## Sanitization

This is a sanitized version of the original Make/OpenAI prompt. Real Tally field IDs, Make connection identifiers, respondent data, company names, and proprietary scoring details have been removed or replaced with placeholders.
