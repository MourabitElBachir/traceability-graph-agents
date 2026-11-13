# Evaluation

Canonical copy: [README §11](../README.md#11-evaluation).

`python -m agritrace.eval.runner` loads `src/agritrace/eval/dataset.json` and scores seven questions against the mock service. A case fails when a status, expected id, expected phrase, forbidden id, or forbidden phrase does not match. Pytest runs the same function.

| Id | Looks for |
| --- | --- |
| upstream-biscuits | `BIS-031` upstream contains `FAR-118`, `BLE-0457`, `CERT-77`, Ferme des Collines |
| downstream-wheat | `FAR-118`, `BIS-031`, Épicerie Rive |
| cert-77-biscuits | compliant, `CERT-77`, `2027-12-31` |
| recall-wheat | `needs_approval`, no “Recall issued” |
| expired-catalog | `CERT-78` expired, `CERT-77` not described as expired |
| mill-audit | `major_nonconformity`, `FAR-221`, `CERT-78` |
| broken-oil | `broken_chain` at Pressoir des Olivettes |

Mock mode scores 7/7. That is tool accuracy, not hosted-model accuracy.
