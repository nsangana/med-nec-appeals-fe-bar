# Customer naming check (FE Bar)

**Decision: anonymized, 2026-11-25** (Naveen's choice, option 2 below).

The repo, bundle, README, docs, evidence and deck use the neutral descriptor "a large multi-state nonprofit health system (HQ Arizona)" on first mention and "the health system" after that. The customer's name, product names, logo and branding are removed. Public payer and regulatory facts are kept (BCBS of Arizona / AZ Blue, AHCCCS, CMS, Medicare Advantage, CARC codes). The customer's public financial figures are kept, with the source described generically. Customer-identifying links are withheld from the public artifact and kept in the private Sheet.

## Sources read (2026-11-25)

1. **FE Bar FAQ** (Glean doc "FE Bar FAQ", author Sabrina Mancini, updated 2026-11-19): https://docs.google.com/document/d/1QNSjA40GGpwrdmV8KxtnvDAN7_eQe5DgsaObpZvehnE
2. **Field Engineering Builder Culture** (Confluence FE space, updated 2026-11-21, includes the BuildPad and FE Bar Q&A): https://databricks.atlassian.net/wiki/spaces/FE/pages/7051739379

## Relevant guidance (verbatim)

FE Bar requirements: "Scrub or synthesize any customer datasets, records, or customer-identifying content before pushing."

FE Bar FAQ, "Does my data and repository need to be customer-safe?":
> "Yes. Build on synthetic data you generate or on a publicly available dataset, never on real customer data. Before scoring, the platform automatically scans your repository, deck, and any linked artifacts for secrets and credentials."

Builder Culture, FAQ "Can I put an internal or FE Bar build into BuildPad?":
> "Yes, if it's generalised, anonymised and uses synthetic data. Never publish customer-specific schemas, names or credentials, and never use public GitHub repositories for customer builds."

Builder Culture, "Development" rules:
> "customer code, schemas, table names, prompts, configuration and data samples must never touch a public GitHub repository or personal account."

## Reasoning

The FE Bar FAQ's rule is about data (synthetic only). The Builder Culture guidance asks for "generalised, anonymised" builds with "zero customer identifiers". A real customer name and logo on the repo and deck conflict with that, so the repo and deck were anonymized.

## What changed

- Customer name, product names and logo removed from the repo, the README, all docs and evidence, and the deck (text, speaker notes and images).
- Evidence sample letters show `[Health System]` with a note that the customer name is redacted.
- Customer-identifying source links (the system's own financial pages and filings, trade-press articles naming it, and tax-filing identifiers) withheld from committed files. The figures are kept, labelled as search-summary or public-filing sources. The full links are kept in the private Sheet.
- Repo and bundle renamed to `med-nec-appeals-fe-bar`. Local filesystem paths are written as `<repo>`.
- Executive roles are unchanged (VP of Revenue Cycle, CDAIO, CFO, Director of Denial Management).

## Options considered (for the record)

1. Keep the customer name as the brief's framing, and accept the reviewer risk under "zero customer identifiers". Not chosen.
2. Replace the name with a generic descriptor across the repo and deck, keeping the industry and payer context. **Chosen (2026-11-25).**
3. Keep the name in a sponsor-facing deck only, with the generic label in the repo and the submission. Not chosen, because the deck is part of the submission.
