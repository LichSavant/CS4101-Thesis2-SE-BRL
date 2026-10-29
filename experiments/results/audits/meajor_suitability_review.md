# MeAJOR Dataset Suitability Review

**Project:** SE-BRL  
**Purpose:** Determine whether MeAJOR can serve as a valid phishing-specific Email benchmark.

## Dataset Summary

MeAJOR contains 108,685 records and 20 columns.

The inspected file contains 108,684 labeled observations from TREC-05, TREC-06, and TREC-07, with one observation missing both source and label.

| Source | Label 0 | Label 1 |
|---|---:|---:|
| TREC-05 | 29,929 | 19,654 |
| TREC-06 | 11,208 | 3,797 |
| TREC-07 | 19,513 | 24,583 |

## Source-Label Assessment

Both binary classes are represented within all three observed source datasets. Therefore, source identity does not deterministically identify the class as it did in the original SE-BRL Email experiment.

However, the underlying TREC corpora were originally developed for spam/ham classification. Although MeAJOR documents its binary target as benign/phishing, these labels do not independently establish phishing-specific annotations for every positive observation.

## Provenance Concern

The inspected file contains only TREC-05, TREC-06, and TREC-07 sources among nonmissing records, although the published MeAJOR description also references Nazario and Nigerian Fraud.

This discrepancy requires clarification before claims about the dataset's source diversity are made.

## Decision

**Status: Not approved as the primary phishing-specific evaluation dataset.**

MeAJOR may be suitable for supplementary evaluation involving broader malicious or unsolicited email detection, subject to clarification of its label semantics.

The primary SE-BRL phishing experiment should use a benchmark with independently defensible phishing labels.

## References

- Cardoso et al. (2026). *MeAJOR: Merged email assets from joint open-source repositories*. Data in Brief.
- NIST Text REtrieval Conference (TREC), Spam Track documentation.
