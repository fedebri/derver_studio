# Survey Schema

This schema summary was derived from the Tally submissions export. The raw export contains respondent-level information and should be kept private.

## Export Overview

- Source file used for analysis: `submissions.csv`
- Parsed rows in the local export: 9
- Parsed columns in the local export: 119
- Primary output: automated diagnostic email sent to the respondent email field.

## Main Field Groups

### Submission Metadata

- Submission ID
- Respondent ID
- Submitted timestamp
- Company name
- Respondent email for feedback delivery

### Strategic Challenges

The first section asks which strategic challenges the company is facing. Tally exports both the combined multi-select answer and one boolean column per option.

Options include:

- Speed up processes and improve operational efficiency.
- Reduce costs and waste.
- Improve the product.
- Increase market share or open new markets.
- Improve customer relationships.
- Address technological transformation.
- Acquire and retain talent.
- Manage risks.
- Improve decision-making and access to information.

The section also includes an optional free-text note about strategic challenges.

### Strategic Blockers

The second section asks which blockers make the strategic challenges difficult to address. The export again includes a combined answer and boolean option columns.

Options include:

- Fragmented systems, silos, and collaboration difficulties.
- Limited financial resources.
- Limited human resources.
- Lack of skills or qualified people.
- Lack of information.
- External pressure such as regulation, unstable markets, or competition.
- Resistance to change.

### Challenge And Blocker Mapping

The third section maps selected strategic challenge areas against specific blockers or severity signals. These fields support the strategic tension calculation by connecting ambition, friction, and operational complexity.

Mapped challenge areas include:

- Process speed and efficiency.
- Costs and waste.
- Product improvement.
- Market share and new markets.
- Customer relationship.
- Technological transformation.
- Talent acquisition and retention.
- Risk management.
- Decision capability and information access.

### Affected Organizational Areas

The fourth section identifies where the reported challenges and blockers are concentrated.

Areas include:

- Production / Operations.
- Logistics and Supply Chain.
- Sales and business development.
- Marketing and communication.
- Customer service / After-sales.
- Administration and finance.
- Human resources / People management.
- Research and development / Product innovation.
- IT and information systems.
- Quality / Compliance / Internal control.

The survey then collects area-specific criticalities, the reference person for each area, and the relevant email address. These fields are operationally useful for follow-up interviews but should be redacted before publication.

### Decision Practices

This section captures how the organization currently produces and uses knowledge for decisions.

Fields include:

- Recurring decision questions the respondent must answer.
- Access to necessary information in a timely and reliable way.
- Decision basis, exported as a multi-select answer and boolean option columns.
- Presence of recognized experts whose knowledge is not formalized or easily accessible.

Decision basis options include:

- Past experience.
- Personal intuition or judgment.
- Advice from external parties.
- Internal reports and metrics.
- External benchmarks or sector trends.

### Analytics And AI Readiness

This section captures the company's orientation toward analytics, data science, and artificial intelligence.

Fields include:

- How strongly analytics, data science, and AI are considered part of company strategy.
- Constraints or risks that could slow analytics initiatives.

Risk options include:

- Initiative cost.
- Limited knowledge of available business and technical solutions.
- Availability of internal resources.
- Limited knowledge of economic incentives.
- Risk of initiative failure.
- Legal or intellectual property concerns.
- Technology security and data protection concerns.
- Low maturity of market solutions.
- Low propensity to integrate into virtual organizations through information exchange along the value chain.

### Company Profile

Profile fields help the prompt contextualize the generated feedback.

- Organization location.
- Number of employees.
- Revenue.
- Sector.
- Market.
- Production planning strategy.

Production strategy options include:

- Engineer to order.
- Make to order.
- Purchase to order.
- Assemble to order.
- Make to stock.

## Calculated Fields

The export includes hidden or calculated fields used by the automation.

| Field | Role |
| --- | --- |
| `Strat_objective` | Intermediate measure of strategic objective intensity. |
| `Block_severity` | Intermediate measure of blocker severity. |
| `Strat_tension` | Intermediate strategic tension calculation. |
| `Functional_load` | Intermediate measure of organizational spread or affected areas. |
| `Score_1` | Final strategic tension score, reported in the email on a 0 to 60 scale. |
| `Info_access` | Intermediate measure of information access. |
| `Decision_make` | Intermediate measure of decision-making basis. |
| `Know_transfer` | Intermediate measure of tacit knowledge and transferability. |
| `Score_2` | Final epistemic maturity score, reported in the email on a 0 to 12 scale. |
| `Feedback_title` | Deterministic feedback title inserted into the email. |
| `Feedback_desc` | Deterministic feedback description inserted into the email. |

## Automation-Relevant Output Fields

The Make scenario reads the following categories from the Tally response:

- Respondent email address for delivery.
- Company name for the email subject and generated feedback.
- `Score_1`, `Score_2`, `Feedback_title`, and `Feedback_desc` for deterministic feedback.
- Open-ended notes and area criticalities for qualitative context.
- Decision practices, analytics orientation, risks, and company profile for prompt grounding.

## Publication Guidance

Do not publish the raw submissions export. It may contain company names, respondent emails, internal business context, and contacts for area owners. For public display, use this schema summary or a synthetic sample with fictional values.
