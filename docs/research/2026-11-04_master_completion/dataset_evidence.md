# Dataset evidence register - November 4, 2026

See [dataset_evidence.json](dataset_evidence.json) for raw/clean SHA-256 values, exact observed schemas, saved audit counts/cleaning logs, implemented target mappings and metadata checks. No raw feature/text records or prediction outcomes were parsed.

Each payload fingerprint/header observation is a VERIFIED DATA RESULT. Saved inventory/count/cleaning entries are HISTORICAL RESULT. Eligibility, source access/license, original-ID lineage and scientific reuse are PENDING SCIENTIFIC APPROVAL. These categories do not establish one another.

| Source | Current intended role | Observed columns raw / clean | Payload identity | Scientific acceptance |
| --- | --- | --- | --- | --- |
| CEAS-08 | auxiliary only | 7 / 7 | Matches tracked LFS identities | Pending; no research authorization |
| Enron | Email legitimate native ham only after audit | 3 / 3 | Matches tracked LFS identities | Pending; no research authorization |
| Nazario | Email phishing positives after audit | 7 / 7 | Matches tracked LFS identities | Pending; no research authorization |
| SpamAssassin | Email legitimate native ham only after audit | 7 / 7 | Matches tracked LFS identities | Pending; no research authorization |
| PhiUSIIL | U1-Ph | 56 / 56 | Matches tracked LFS identities | Pending; no research authorization |
| UCI Phishing Websites | U1-UCI | 31 / 31 | Matches tracked LFS identities | Pending; no research authorization |
| ISCX-URL2016 All | historical outside active Table 4.7 | 80 / 80 | Matches tracked LFS identities | Pending; no research authorization |
| ISCX-URL2016 Phishing | historical outside active Table 4.7 | 80 / 80 | Matches tracked LFS identities | Pending; no research authorization |
| Phishing Website Dataset (Putra; approved content-bearing Web) | Web E1/E2/E3 | no identified payload | Not established | Pending; no research authorization |

| Historical assignment metadata | Observations | Groups | Mixed-target groups | Development / calibration / test | Recorded group crossings |
| --- | ---: | ---: | ---: | --- | ---: |
| email | 38759 | 21601 | 0 | 27129 / 5815 / 5815 | 0 across partitions; 0 across folds |
| phiusiil | 235795 | 220086 | 54 | 165089 / 35358 / 35348 | 0 across partitions; 0 across folds |
| uci | 5849 | 5785 | 64 | 4094 / 878 / 877 | 0 across partitions; 0 across folds |
| iscx | 14823 | 14823 | 0 | 10375 / 2224 / 2224 | 0 across partitions; 0 across folds |

All four manifests have unique supplied observation IDs and no reserved fold values. These are metadata facts, not proof of duplicate, campaign, template or domain independence. No assignments were regenerated.

The historical Email manifest includes CEAS-08 ham, while current approved primary construction uses Nazario positives and Enron/SpamAssassin ham, with CEAS-08 auxiliary. Therefore its 38,759 records cannot be adopted as the new primary population. Source identity determines the implemented constructed target; excluding explicit source columns does not remove content/source shortcuts.

PhiUSIIL's observed 56 raw columns do not imply 56 approved predictors: IDs, native labels, string fields and provenance-sensitive columns require the actual audited dictionary. Its technical branch cannot substitute for the absent content-bearing Web dataset. UCI -1/0 feature codes are native values where their individual domains permit; the Result class-definition citation is still pending.

ISCX remains historical and outside the active approved Table 4.7 exports. The abandoned dataset remains excluded. No replacement source was acquired.

Missing records are concrete: source_snapshot_id/acquisition/license/access evidence; exact source-backed labels; original-ID reason-coded screening/attrition and duplicate families; reconciled source-permitted groups and split acceptance; actual ordered feature dictionaries; development delivery/custody and exposure-aware claim scope. The existing UCI scientific acceptance packet details its individual decisions.

