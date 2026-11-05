# Public release and model limitations

Prepared 5 November 2026 from the frozen v4 research folder. Original files were left unchanged. This is a curated distribution, with a new public manifest; it is not the original 129-file release.

Core economic/controller code, data extracts and numerical experiment results retain their scientific values. The report and summary have been edited for publication without changing the numerical findings. Packaging adds a public verifier and exact-source retrieval helper. The release inventory excludes optional source caches. Two primary-source tests explicitly skip without those caches; `--with-sources` requires the complete original evidence and fails on missing or changed bytes. Local source-file verification is separate from the published-file inventory.

The distribution includes the model, numerical evidence and research documentation. Development files and third-party source caches are excluded. Historical source-audit assertions are retained as previously generated evidence, not a newly executed source audit. The retained report describes the original research release; use the public README and `verify_public.py` for this distribution's commands and assurance scope.

## Interpret the result carefully

- Selected cash 20 is the least-cost passing candidate on the declared grid, not a continuous optimum or a company cash recommendation. At cash 1 through the disclosed cash anchor, several rule candidates have 2/1,000 failures and a simultaneous upper bound about 1.0399%, narrowly missing the 1% screen.
- At selected cash both policies meet the model-conditional test upper-bound target; lower MPC cost comes with worse reliability. There is no matched-risk efficiency or universal dominance claim.
- Timing concentration is assumed. In the existing common-cash stress with true concentration 45 versus controller assumption 180, failure frequencies are 11.67% for the rule and 46% for MPC.
- Sparse cumulative industry payments cannot establish individual claim deadlines. Three related-event groups cannot establish a universal payment curve; the largest held-group transfer error is about 32.83 percentage points.
- Monte Carlo intervals do not cover parameter, public-data measurement, portfolio-perimeter or structural model error. No full-firm solvency adequacy or regulatory compliance follows.

## Checks

Original-release review: 58 unit tests, 28 frozen path replays and 82 cross-artifact checks passed; 129 original release hashes matched. The full long-running study was not rerun. Public-package checks are reported separately in the accompanying handover review; no remote GitHub CI pass is claimed.
