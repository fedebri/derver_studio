# Derver Studio

Applied analytics, automation, and diagnostic prototypes for turning fragmented business information into operational intelligence.

This repository collects selected work developed within Derver Studio, a practice focused on helping organizations structure their data, clarify decision processes, and deploy pragmatic analytics and AI-enabled workflows.


## Projects

### 1. SKU Inventory Data Integration

Path: `sku_inventory_integration/`

An anonymized SKU-level data integration workflow for supplier feed reconciliation, ecommerce catalog alignment, and operational data quality control.

The project demonstrates how heterogeneous inventory and catalog sources can be ingested, standardized, merged, validated, and converted into business-ready outputs. It includes both an exploratory notebook and a production-style Python script designed around scheduled updates.

Core themes

* Supplier feed reconciliation
* Ecommerce catalog alignment
* SKU identifier normalization
* Data quality checks
* Inventory availability logic
* Operational review prioritization

Representative artifacts

* merge_sku_updated.ipynb: exploratory notebook showing the end-to-end integration workflow.
* hourly_sku_data_update_demo.py: production-style script for scheduled SKU data updates.

⸻

### 2. Survey Automated Response

Path: `survey_automated_response/`

An AI-assisted diagnostic survey workflow built with Tally, Make, OpenAI, and automated email delivery.

The workflow turns a completed business diagnostic survey into a respondent-specific feedback email. It combines deterministic scoring from structured answers with a qualitative reflection generated from selected open-text responses and company profile fields.

Core themes

* Business diagnostic survey design
* Strategic tension scoring
* Epistemic maturity scoring
* Tally and Make automation
* OpenAI-assisted qualitative synthesis
* Personalized feedback generation

Representative artifacts

* README.md: workflow explanation and design logic.
* PROMPT.md: sanitized OpenAI prompt structure.
* docs/survey-schema.md: questionnaire and calculated-field map.
* make_survey.blueprint.simplified.json: simplified Make scenario blueprint for documentation and portfolio review.


## Repository structure

```text
derver_studio/
├── sku_inventory_integration/
│   ├── README.md
│   ├── merge_sku_updated.ipynb
│   └── hourly_sku_data_update_demo.py
│
├── survey_automated_response/
│   ├── README.md
│   ├── PROMPT.md
│   ├── docs/
│   ├── make_survey.blueprint.simplified.json
│   └── make_survey.blueprint.json
│
├── README.md
└── .gitignore
```


Status

The repository is not intended to provide production-ready client systems. It is intended to make selected technical and methodological patterns visible in a public and anonymized form.

Privacy and publication notes

All public materials should be treated as sanitized documentation.
Where a workflow originated from private work, the public version preserves the structure and design logic while replacing sensitive data with safe examples or documentation-oriented representations.