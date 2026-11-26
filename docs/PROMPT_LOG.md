# Prompt log — how I directed the AI (curated)

Built with Claude Code orchestrating parallel sub-agents, and Isaac for building and reviewing the solution and the Google Slides deck (sessions `e2e3204c-874a-4e35-bf06-2aa699e64087` for the build and `b0cc9995-d83b-4627-b4ee-eed4b81318ec` for the bundle, clean run and final passes).
These are curated excerpts from my prompts. They are shortened where indicated (…), with spelling corrected and
customer or individual names redacted; the meaning is unchanged. Where I combined or materially reworded several
messages, the entry is marked *(paraphrase)* and is not in quotation marks.
Additional detail on the decisions and resulting changes is in `docs/STEERING_LOG.md`.

## 1. Set the scope and the working model
> "Can you look at this prompt (`refined_prompt.md`) and start building a solution for the same in my fevm-appeals-hackathon workspace. Create a new schema, volume, tables, files etc., whatever you think is needed to be able to show the automated medical-necessity filing use case which helps with timely filing of appeals for denied claims. Fan out subagents and please don't try to go into the rabbit holes and create slop."

→ Shared contract and findings log; parallel agents for data/Lakeflow, GenAI, Lakebase, Genie/governance and the app; orchestrator verifies agent claims before reporting. (`docs/SPEC.md`, `docs/FINDINGS.md`, `evidence/08_job_run.md`)

## 2. Ground it in the real customer problem
> "This is some more context on how I built the solution … look at the README to understand the flow. And this is the transcript … Use a subagent to gather this context and send it to the agents if you feel it's necessary."

→ Requirements distilled by role: an automated morning worklist, no manual prompting, and a deterministic data sheet beside every AI-drafted letter so a reviewer can verify it at a glance. (`docs/CUSTOMER_CONTEXT.md`, `pipeline/25_data_sheet_facts.sql`)

> "I don't have [health system]-specific numbers; they are based out of Arizona and are across multiple states, so make the decision based on publicly available information."

→ Appeal windows were modeled from public rules — Commercial 180 days, Medicare Advantage 65 days and Arizona Medicaid 60 days — but are explicitly treated as assumptions because provider-contract terms may differ. (`data/SOURCES.md`)

## 3. Diagnose platform issues from the live app
> "Need to fix this error in the chatbot: Agent endpoint error (403): You do not have permission to query the endpoint … Is it a permissions issue on the endpoint?"

> "Genie in the app seems to be not functioning … Have you embedded the Genie Agent here or are we using the Conversations API?"

> "Are we creating a model service or using legacy AI Gateway endpoints?"

→ Root causes found and fixed: the chat endpoint was not bound to the app (CAN_QUERY added); the `genie` OAuth scope never reached the user token, so Genie runs as the app service principal (trade-off documented); UC functions re-created mid-deploy broke agent auth, so creation was made idempotent. (`evidence/09_chatbot.md`, `evidence/06_app.md`, `lakebase/AUTH.md`)

## 4. Make governance real, not decorative
> "For now create it as a workspace-level group, and add me to it." … "I am not the account admin for the Databricks account, so I am OK with the workspace group for this demo. Let's harden the build with the column mask, and the quotes, and add the MLflow tracing."

→ PHI column masks on seven columns; MLflow LLM-judge evaluation; quote-level checks; least-privilege cleanup, including revocation of a broad grant. (`evidence/13_column_masks.md`, `evidence/14_mlflow_genai_eval.md`, `evidence/02_governance.md`)

## 5. Pressure-test the business case
> "Let's do the business case phase 2." … "What do you recommend for the deck — what would appeal more to an exec?"

→ The starting $12.8M hypothesis was not supported as originally constructed. I replaced it with sourced Floor / Likely / Ceiling scenarios of $2.2M / $4.3M / $8.7M, while clearly labeling the Likely scenario's unsourced 2.0× dollar-weighting assumption. (`docs/business_case/MODEL.md`, `docs/business_case/DECK_NUMBERS.md`)

## 6. Check readiness honestly
> "So is my build ready to be submitted? Are there any changes you would make to my architecture? Is it all looking solid?"

→ Value-for-effort hardening ranked and applied. Judge context corrected; groundedness improved from 83.3% to 98.3%, and a drift test was added. (`docs/READINESS.md`, `docs/CODE_REVIEW.md`, `evidence/14_mlflow_genai_eval.md`)

## 7. Keep the customer and the evaluator in mind
> "The solution is mainly to help the RCM operations folks … have a pipeline that is automated instead of searching through multiple surfaces or systems to be able to file appeals, right? Do you agree?" … "At the same time also help recover revenue?"

→ Title chosen: "Automate the Appeal. Recover the Revenue." (`docs/deck/DECK.md`)

> "Would you present this deck to an exec? It looks unpolished … look at this slide … that looks like a solid intro."

> "What do you think of building a reference architecture for the solution that an exec would be able to digest … I don't want to make the deck lengthy. I was thinking from a solution point of view to demonstrate the value of Databricks. Run this as a subagent and parallelize work."

> "The first slide should have my name at the bottom, the ask for the POC should be at the end, after I demo the value. The second slide should be the agenda."

> "Does the slide deck now speak to the solution I built? I want it to be flowing rather than disjointed."

→ Deck rebuilt on the Databricks template; one exec reference-architecture slide replaces a text-heavy one; a 12-slide story threaded by one denied claim (overview plus detailed reference architecture); pilot and ask last. (`docs/deck/DECK.md`, `docs/deck/ARCH_SLIDE_SPEC.json`, `docs/deck/FE_Bar_Medical_Necessity_Appeals_POV.pdf`)

## 8. Use the product as a reviewer would
> "When I click on the case file the rendering is not perfect; it doesn't show a proper pop-up, it opens a window which looks clumsy and I'm unable to scroll up or down."

> "When I open and make edits to the letter, what benefit do I have with that feature, as the PDF is not getting updated in real time? Also the Appeals Agent and Genie panel on the right … I need to scroll down to type my question. Is that something we should fix?" … "Explain if this is too much of a heavy lift." … "Which would make the demo look slick?"

> "I didn't see the Appeals Agent and Genie alignment completed; they are still not the best user experience."

> "Do you think we should have a filter for the Recommendation section to filter between Warranted, Not Warranted, or based on Expected $?" … "Use parallel agents."

→ Case-file dialog rebuilt; edited-letter preview with highlighted changes and a downloadable final letter, with no new permissions; a full-height assistant sidebar after the first fix fell short; worklist filters with counts, verified against Lakebase. (`evidence/06_app.md`)

## 9. Make the cost and the deployment defensible
> "Also, in parallel, can you create a cost dashboard for this solution — call it Appeals Automation Agent Insights … that shows the costs of running pipelines, agents, apps etc. … My thought process is to cover my base if the customer asks me how did you come up with the cost for automation." … "What do you think about my thought process?"

→ AI/BI dashboard on `system.billing` with direct vs allocated labels and a method page; a cost-at-volume table was added after the critique. Cross-checks to the measured figures: $0.069 LLM, $0.10 variable and $0.52 fully loaded per appeal at 60 a day, falling to $0.14 at 600 a day (list price). (`evidence/15_cost_dashboard.md`, `dashboards/cost_views.sql`)

> "Can we ensure the bundle has all the needed components, also deploying the dashboard?" … "For Genie and the dashboard, I thought we could export the configs as JSON and then use bundles for them?" … "There are bundle examples here if you need references." (pointing to the public Databricks bundle-examples repository)

→ 17 live resources bound into the bundle — dashboard and Genie space from exported JSON, schema, volumes, the Lakebase Autoscaling chain and synced table, registered model, vector index and chat endpoint — with a verified no-op plan (0 add / 0 change / 0 delete); the app, roles and grants run through `scripts/deploy_all.sh`. (`evidence/16_bundle_deploy.md`, `resources/`)

## 10. Keep it reproducible and clean
> "I want this content of the session written to a folder in my home directory, so I can re-use it if I restart the session."

> "I assume you are updating the evidence on how I'm steering the AI to get to the end state I'm after, for both the solution and the deck?"

> "You are keeping all the context clean in the git repo, right? There is no stale data or checkpoints?"

> "I want the prompts which make sense and have technical meaning … I want to review before you publish. I don't want each and every single line, but rather a log showing my ability to navigate to get things done."

→ Handoff pack and playbook kept outside the repo; steering log and this curated prompt log (reviewed before commit); current-only evidence with superseded runs pruned to git history. Both repositories are anonymized in their current files; the public snapshot carries a single clean commit, while the private submission repository keeps its full working history. (`docs/STEERING_LOG.md`, `evidence/EVIDENCE.md`, `docs/SESSION_LOG.md`)
