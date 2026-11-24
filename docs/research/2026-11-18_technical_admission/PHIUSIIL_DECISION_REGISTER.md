# PhiUSIIL development decisions — reported joint direction

Attribution: the current user reports that both researchers discussed and agreed
to the most defensible implementation compatible with the approved methodology.
This records that report and the implementation choices below, not independently
verified signatures, exact-file acceptance, a trusted digest or fitting permission.

| Decision | Implementation and evidence | Alternative and consequence |
| --- | --- | --- |
| Identity | Reuse the hash-bound 165,089-position reconciliation. Adopt original-snapshot/file/position `prospective_id` identifiers with a lossless historical-ID alias ledger. All selected source cells match exactly or by exact declared-numeric decimal equality. No independently authenticated historical execution or global uniqueness claim. | Historical rank alone cannot authenticate source identity. No new raw reconciliation or reserved-row comparisons. |
| Assignments/conflicts | Preserve all original development memberships, groups, targets and five folds. Keep all 36 mixed-label groups intact. Only normalize integral fold representations. | Dropping/relabeling conflicts or reallocating groups would change the population and requires a separately accepted policy. |
| Exposure/claims | Treat reuse as exploratory, previously exposed. No untouched holdout, final validation, behavioral-indicator or Transformer-reasoning claim. | Formal confirmation requires independently evidenced unexposed material and its accepted protocol. |
| Technical dictionary | Freeze the ordered ten source fields below as a conservative URL-structure U1 subset. Select original finite numeric values, not recomputed corpus statistics. Exclude every other source field. Official metadata binds numeric roles; the approved methodology's technical branch and feature-boundary contracts permit explicit source-appropriate dictionaries. | The 50-field candidate would include source-engineered reference/probability/similarity features with unresolved derivation/exposure dependencies. It is not adopted. This ten-field subset does not reproduce a full-source benchmark. |
| Missingness/encoding | Numeric scalar inputs only; reject missing, non-finite, nonnumeric or nonintegral values in this count/flag subset. Preserve source values. No imputation, scaling, encoding fit, tuning or feature selection during delivery. Any later scaling is training-fold-only under accepted experiment settings. | Silently filling values or deriving parameters from all folds/reserved records would be unsupported. |
| Behavioral availability | The technical-only branch's existing dispatcher supplies Unavailable with zero support/availability bits. No lexical/content inference from technical fields. | E2/E3 comparisons cannot establish behavioral contribution on this population. |
| Admission boundary | Produce the five genuine development input files and checks. Do not create `feature_acceptance.json`. The existing D-features gate additionally requires a complete accepted three-role source-locator population/assignment set; only development originals are verified here. | Never fabricate reserved native labels/locators to satisfy three-role coverage, or treat a self-computed digest as independent acceptance. |

Ordered numeric fields: `URLLength`, `DomainLength`, `IsDomainIP`, `TLDLength`,
`NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`, `NoOfLettersInURL`,
`NoOfDegitsInURL`, `IsHTTPS`. FILENAME, labels, IDs, groups and partitions are
metadata/excluded predictors. No raw URL, domain string, title or message is
exported. FILENAME is never exported as a predictor or treated as a unique key.

Supporting evidence: `d-features-delivery-status.json:latest_reconciliation`;
`phiusiil/official-metadata.json`; `phiusiil/label-verification.json`;
`researcher-authority-matrix.json` in the preceding admission directory; approved
proposal PDF pp.63–66/Table 4.4 as cited there. Controlling implementations:
`ml/preparation_execution.py`, `ml/preparation_integrity.py`,
`ml/notebook_contracts.py`, `ml/development_experiments.py` and
`ml/research_protocol.py`. These implementation decisions do not change any gate.

Minimum remaining acceptance: authenticate the upstream expected original-ID
universe and complete three-role metadata (without opening reserved predictors),
then provide the actual dated exact-file no-fit acceptance through a trusted
operator with independently trusted digest. After admission, fitting separately
requires an exact frozen experiment/budget and attributable fitting receipt.
