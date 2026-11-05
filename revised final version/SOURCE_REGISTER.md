# V4 evidence register and actuarial mapping

Checked 14 October 2026. Local source downloads are for this private research folder; do not assume redistribution rights. Numeric extracts are attributed public facts; model choices are separately identified. All model money is a normalised 100-unit pool, not a company's actual million-dollar forecast.

## Primary sources

1. Tower Limited Annual Report 2025, official issuer PDF: https://www.tower.co.nz/wp-content/uploads/2025/11/FINAL-FY25-TWR-Annual-Report.pdf . Downloaded complete; SHA256 and bytes recorded in data/source_retrieval_manifest.csv. Printed pages 43/45/62/68/80 correspond to PDF pages 45/47/64/70/82. Comparative 2024 figures are from the SAME report, not an independent second issuer.
2. ICNZ 2023 NZ event snapshots: exact URLs are retained per row in data/payment_evidence.csv; the previous five-row source extract is preserved as data/nz2023_original_snapshots.csv. Two related weather events form ONE held-out group. The June date is a publication-date proxy; December estimated costs are retrospective reference denominators, not ultimates.
3. Kaikoura paid/received table, as of 30 June 2017: https://www.icnz.org.nz/industry/media-releases/private-insurers-paid-out-0-5-billion-kaikoura-earthquake-claims/ . Exact paid 522,067,833 NZD; estimated claims 1,876,800,143 NZD. Perimeter excludes separately EQC-managed claims and offshore insurance.
4. Kaikoura 30 November 2017 status: https://www.icnz.org.nz/industry/media-releases/settlements-reached-for-82-of-kaikoura-claims/ . MORE THAN NZD1bn paid is a censored lower bound. The 82% is fully/partly settled CLAIM COUNT, not paid dollars. It is not used as a payment proportion.
5. ICNZ historical disaster list: https://www.icnz.org.nz/industry/cost-of-natural-disasters/ . Nominal Kaikoura cost 2,270m is the retrospective reference; do not substitute the inflation-adjusted column. Later reference and June table scopes may not perfectly match; the transfer check is qualified accordingly.
6. ICA Australian 2022 flood, 3 May: https://insurancecouncil.com.au/resource/updated-data-shows-2022-flood-was-australias-costliest/ . Rounded AUD580m paid, 3.35bn estimated cost. A +/-5m interval reflects displayed rounding, not sampling error.
7. ICA 28 June: https://insurancecouncil.com.au/resource/2022-flood-now-third-costliest-natural-disaster-ever/ . Rounded 1.5bn paid, 4.8bn estimated cost; paid interval +/-50m.
8. ICA 29 July: https://insurancecouncil.com.au/resource/2-billion-in-flood-payments-already-made-by-insurers/ . MORE THAN 2bn paid; 5.134bn estimated. Lower bound is not treated as an exact point.
9. ICA 30 November: https://insurancecouncil.com.au/resource/three-year-weather-bill-reaches-12-3-billion/ . Rounded 3.54bn paid; cost MORE THAN 5.65bn. The 5.65bn research reference is explicitly lower/rounded, not final ultimate. Paid rounding interval +/-5m. Event began before its 26 February 2022 declaration and has multiple waves; clock date is an approximation.
10. NZX clearing: https://www.nzx.com/services/nzx-clearing/about and https://www.nzx.com/services/nzx-clearing . T+2 on-market cash settlement and coverage including NZX debt support a two-business-day case. This does NOT establish that all Tower holdings are on-market, executable at assumed spreads, or unavailable for same-day OTC settlement. Lag 0/1/5 are tested.

The September 2022 ICA $2.81bn/54% 'claims finalised' statement is deliberately EXCLUDED as paid-cash evidence because the wording does not unambiguously identify cash paid. Claims counts, assessed amounts and payments are not interchangeable.

## Company facts and mapping controls

Official 2025/2024 cash is 71.047/75.390m NZD. Fixed-interest investments are 389.191/367.472m, excluding 0.034m property investment in EACH year. The 2025 research pool is 460.238m; using total investments without excluding property would overstate financial liquidity.

Restricted cash is PNG 3.7m plus Solomon Islands 3.8m in 2025 (7.4m plus 3.3m in 2024). These amounts cannot currently be used outside those countries. Restricted cash is a separate stock, not usable recourse cash. A no-restriction sensitivity is an alternative perimeter, not the base.

Opening cash + operating + investing + financing + FX reconciles ending cash in both comparative years. Gross claims/service cash and reinsurance cash are recorded separately; 2024/25 annual totals do NOT identify event collection lags. The simulated recovery-lag mixture remains hypothetical and future recoveries are NOT counted in policy forecasts until received.

The maturity table is DISCOUNTED. It is not copied into nominal payment demands without explanation. The scenario conversion uses midpoint undiscounting at an explicitly approximate interest-income proxy. The negative -0.186m 5+ year bucket is excluded from gross positive payment demands, not invented as negative claims. Model nominal background obligations therefore do not equal reported discounted LIC. The original discounted facts, conversion rate and exclusions are released in data/company_anchors.json. This is not an IFRS reserve reconstruction.

The source reports 2.56% END-DATE deposit rate in 2025. Interest income divided by mean 2024/25 cash-plus-fixed-interest pool gives a historical aggregate proxy, not a marginal bond yield or expected excess return. Its difference from the deposit rate is used ONLY as a central scenario; 0.5/2 percentage-point spread sensitivities remain necessary. Historical data are not current executable investment quotes.

No contractual bank facility, execution cap, marginal dealing spread or security-level financing covenant has been established. Primary facility is zero; a 3-unit, 7.5%-rate, 0.2%-commitment, secured revolving line is clearly HYPOTHETICAL. Non-disclosure is not evidence that Tower has no funding access. No issuer-specific recommendation is made.

## Transfer tests, not a validation certificate

11 snapshots, four event labels, three event groups. The two NZ 2023 events stay together in every leave-group-out split. Censored lower bounds contribute one-sided loss, not fabricated exact observations. All reported cost references are retrospective, incomplete and possibly perimeter-dependent. Group-held-out errors test portability of a common payment shape; they cannot validate private contractual due dates or a specific insurer model.

The main simulation retains the NZ weather group as a stated application family. AU flood timing is an external alternative; Kaikoura is a qualified cross-peril check. Failed transfer results are retained and restrict applicability. The noisy-loss-report process, severity prior, daily allocation and execution/funding assumptions remain synthetic. More source files do not turn them into empirical measurements.


V4 retrieval update: the April 2023 ministerial-submission PDF was downloaded directly and the exact 147,068,198 / 1,155,301,657 table verified on PDF page 2. The v3 retrieval limitation is now resolved; the original extract remains preserved for provenance.

The source liquidity table's at-call figure (71.107m) differs from balance-sheet cash (71.047m); it is not silently forced to match. The mapping uses balance-sheet cash and fixed-interest holdings, and uses the liability maturity shape separately. It does not reconstruct every asset-maturity bucket.

Base simulation credits aggregate income daily as a cash-flow approximation. Source interest income is NOT proof of daily coupon availability. A separate case books all earned interest as an inaccessible receivable, with no within-horizon cash credit; a zero-capacity less-liquid bucket case also tests deposits/holdings that cannot be sold. These are assumption bounds, not verified contractual schedules. Actual coupon, bank-credit and instrument maturity dates remain a deployment gate.

## External professional context (not compliance certification)

IAIS, Application Paper on Liquidity Risk Management, 29 June 2020, sections 2–7: https://www.iais.org/uploads/2022/01/200629-Application-Paper-on-Liquidity-Risk-Management.pdf . This guidance discusses governance, entity/location transfer constraints, stress analysis, unencumbered liquid assets, contingency funding and reporting. The project uses those themes as challenge prompts; it does not implement all of them or establish regulatory compliance. The paper is guidance and examples, not itself a new binding standard.

PRA, SS5/19, Liquidity risk management for insurers, November 2024 document: https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2024/ss519-november-2024-update.pdf . This is UK supervisory context, not a rule asserted to govern the NZ/Australia example. Full company cash-flow coverage, accountable ownership and operational funding plans remain outside this simplified research engine. A document mapping is not regulatory or professional approval.

Both primary PDFs are cached and hashed. No model parameter, legal deadline or company financing access is calibrated from these guidance documents.


## 2 November 2026 executable verification amendment

`audit_real_data.py` now re-extracts 40 comparative-year company values from the
original Tower PDF (one-based PDF pages 45, 47, 64, 70, 82), checks the Kaikoura
received/settled dollar totals directly from the primary HTML table, validates all
11 payment records structurally and verifies hashes/lengths for 15 cached sources.
`results/primary_source_assertions.csv` records field, year, units, page and source
hash. Other event transcriptions remain subject to manual semantic review.

A live re-download of the same historical annual report on 2 November 2026 matched
the frozen 17,520,646-byte file, SHA256
903f3b618890c5e68fb0df9d1547e1d0ac1d29ac68faebf54e6892947fc7a308.
See `results/live_source_receipt.json` for its URL and UTC timestamp. This is source
consistency verification, not new 2026 financial data or empirical daily-liability
calibration. The primary source is the issuer annual report listed above.

`retrieve_sources.py` stages future downloads and comparison receipts under
`work/source_refresh/`; it never overwrites the frozen source snapshot or its
manifest. A changed live page needs review rather than automatic acceptance.
