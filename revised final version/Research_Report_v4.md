# Economic liquidity buffers under settlement delay and partial loss information
## Source-anchored actuarial decision research, v4

14 October 2026; public documentation revised 5 November 2026. Working paper on a closed-book liquidity pool, rather than a complete insurer or regulatory capital model.

## Executive finding

V3's all-cash result was driven by a synthetic capital penalty. V4 removes that mechanism: minimise measured cash/pending-receipt opportunity cost, dealing expense and financing expense SUBJECT TO a payment-reliability screen. Both zero and all-cash endpoints remain allowed. Physical settlement delay and restricted cash are explicit. No preferred interior result is imposed. Final training-selected outcomes are:

| Policy | Cash | Test failure % | One-sided 95% upper % | Mean financial cost |
| --- | --- | --- | --- | --- |
| rule | 20 | 0 | 0.099808 | 0.04249 |
| mpc | 20 | 0.23333 | 0.43782 | 0.042392 |

The strong simple rule is the safer research reference in this experiment. At common cash 2 it has 5/3000 failed paths versus 151/3000 for MPC. At their separately training-selected cash, the counts are 0 versus 7. MPC's lower measured cost does not establish a safety-matched efficiency improvement. Its short lookahead, payment-timing shocks and revising risk envelope expose a practical model-risk failure, despite high average forecast coverage. Do not deploy MPC on the strength of these results.

A model-conditional interval is not real insurer certification. The common-cash experiment and complete training frontier are retained below, including any unfavourable result for MPC. Costs are in normalised pool units; multiply by an actual verified liquidity-pool scale only after validating that perimeter.

## 1. What changed, and the decision boundary

The question is how much immediately usable cash to hold in a fixed-income liquidity pool, and how a controller should convert holdings when ultimate losses and future payment dates are unobserved. Initial cash is chosen before the particular synthetic event outcome is known. Scenarios are CONDITIONAL ON one catastrophe at inception, not a calibrated annual occurrence process. This is event-conditional preparedness, not an unconditional shareholder portfolio optimum.

Initial pool is 100, including separately restricted cash. The remaining investment pool is split into two assumed execution buckets, 70/30: lower- and higher-cost fixed income. These are NOT inferred government/corporate proportions for Tower. Constant marks and specified accrual rates isolate liquidity economics; full duration/default/FX risk, underwriting, premium renewals, dividends and taxes are outside this closed-book pool. Solvency is a latent-truth simulation diagnostic, not the objective or an SCR calculation. No full-company adequacy judgement follows.

## 2. Expanded public evidence and adverse transfer results

The release contains 11 attributed snapshots across four event labels and three related-event groups: Auckland Anniversary and Cyclone Gabrielle 2023 (kept together), Kaikoura 2016, and Australian East Coast floods 2022. The last two provide genuinely different event/peril/jurisdiction evidence. Rounded numbers are intervals; more-than amounts are lower bounds; settled-claim COUNTS are not paid-dollar fractions. The ambiguous September 2022 'finalised' amount is excluded.

Weibull timing is fit to cumulative paid/reference fractions with interval-distance loss; lower-bounded observations are not forced into exact points. References are retrospective reported costs, not final known ultimates. Related NZ events never appear on opposite sides of a grouped split. Main simulation uses the declared NZ weather family; AU timing is an external alternative and Kaikoura a qualified cross-peril check. The largest group-held-out interval error is 32.83 percentage points. This FAILS to support a universal cross-peril curve. More data therefore restrict the scope rather than falsely validating the original model.

[FIGURE:figures/event_transfer.png]

Dates, currencies, source URLs, displayed precision, bounds and qualifications are in data/payment_evidence.csv. The AU event has multiple waves and a declaration-date clock; its 5.65bn reference is explicitly lower/rounded. The Kaikoura private-insurer and later reference perimeters may differ. These controls are descriptive transfer tests, not contractual due-date validation. Daily demands within sparse public reporting intervals are synthetic and are treated as due ONLY by model assumption.

## 3. Real-company anchors and accounting transformations

Tower's official 2025 report provides two comparative years, not two independent insurers. We retain the complete official PDF, page locations and retrieval hashes. The 2025 balance-sheet cash is NZD71.047m; fixed-interest holdings are 389.191m. The 0.034m property investment is excluded. Restricted PNG and Solomon Islands cash totals 7.5m. This gives a 1.6296-unit restricted share and 13.8074-unit accessible-cash reference per 100 financial-pool units. The disclosed cash level is descriptive, not a benchmark of management competence.

| Year | Opening cash | Operating | Investing | Financing | FX | Closing cash | Residual |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | 75.39 | 143.76 | -46.954 | -102.84 | 1.69 | 71.047 | -1.4211e-14 |
| 2024 | 65.311 | 145.19 | -116.57 | -16.473 | -2.067 | 75.39 | 1.4211e-14 |

The cash bridge reconciles in both years. Gross claims/service payments and reinsurance receipts remain separate. Annual recovery totals cannot identify an event cash-collection distribution. Source maturity buckets are discounted; V4 uses an explicit MIDPOINT UNDISCOUNTING scenario, not an unexplained nominal copy. The negative -0.186m long-tail bucket is excluded from gross positive demands. This produces background nominal obligations 26.4107, 13-week payments 11.3346, 26-week payments 16.2380, and 52-week payments 20.8297. Discount-conversion sensitivity is released; this is not an IFRS reserve reconstruction.

Interest income divided by mean two-year financial pool gives a historical proxy of 3.636%; the disclosed deposit rate is an END-DATE 2.56%. Their 1.076-percentage-point difference is ONLY a central scenario, not an identified marginal expected bond premium. Endpoint-versus-period measurement and portfolio composition prevent stronger inference. Spread sensitivities 0.5 and 2 percentage points are retained. These are historical source anchors, not current executable quotes.

The source does not establish a bank facility available to this model. Primary facility is ZERO, without claiming the company lacks funding access. The optional 3-unit secured revolver, 7.5% financing and 0.2% commitment fee are hypothetical. Restricted cash cannot pay central-pool demands; local offshore liability matching is not reconstructed. Group anchors plus a conservative central-pool perimeter must not be represented as Tower internal optimisation.

## 4. Daily stock-flow engine and economic objective

A business day begins with dated trade settlement and actual recovery cash, then accrual, current reports/current demand, control, and FIFO claim payments. Sold inventory is removed immediately; a net sale receivable remains until settlement. It cannot fund a claim early or be resold. Restricted cash and its income remain inaccessible. The base two-business-day lag is supported as an on-market NZX case, not established for every actual holding. Lags 0/1/5 and capacity changes quantify the assumption. Spreads/caps are declared scenarios, not extracted transaction data. The base credits aggregate income daily as a cash-flow approximation, not verified coupon dates. A no-income-cash case records earned interest as an inaccessible receivable; a locked-bucket case permits zero sales. Actual coupon and deposit-credit dates remain an operational gate.

Optional debt capitalises stipulated interest, is secured against retained lower-cost holdings, and is callable on a borrowing-base deficit and at the study end. Commitment cost is paid even if unused. Algebraically cancelling LP draw/repayment pairs are netted before execution so paper refinancing cannot create capacity. Actual cash and economic own-funds P&L are independently rolled from opening stocks and flows, including pending receivables, provisions, recoverables and financing. Raw ledgers expose every term. Claims remain obligations after failure and the horizon.

For each day, financial cost is cash times the asset-minus-cash rate difference, plus zero-yield pending receivables times the asset accrual rate, plus execution, accrued finance and commitment expense. Cash interest and asset accrual are credited once to the cash ledger; opportunity cost is a comparator measure, not a second cash debit. There is NO monetary shortfall or capital-warning penalty. Reliability is separately constrained. This removes the v3 incentive to buy less market-risk exposure merely to avoid an arbitrary capital charge.

[FIGURE:figures/cash_tradeoff.png]

## 5. Partial information and forward control

True ultimate catastrophe loss is lognormal with median 30 and log SD .45, synthetically specified. Every five business days, a noisy log report arrives; log-report SD .55 is also synthetic. A Gaussian REPORT-ONLY Bayesian filter updates latent ultimate-loss belief. It deliberately does not claim a fully calibrated filter incorporating every paid/notification datum. Known cumulative demands form a hard lower bound in forecasts. Neither true ultimate nor future realised payment/recovery arrays enter the immutable controller observation.

Future payment envelopes combine a selected ultimate-loss posterior quantile with conditional Dirichlet/Beta cumulative timing quantiles. Their combination is not an exact joint predictive quantile. Turning the cumulative envelope into increments yields a deterministic risk scenario, not a stochastic scenario tree. Receding forecast revisions and misspecification can defeat this approximation; out-of-sample safety is therefore screened and forecast coverage assessed by independent PATH clusters, not falsely independent daily windows. Recovery cash is not counted in forecasts before collection.

The strong simple rule is income-aware forecast base-stock control: cover the chosen horizon's net cumulative payment envelope, dated pending receipts and conservative coupon income, executing lower-cost holdings first. MPC uses the SAME information and a finite-horizon linear plan. First minimise forecast overdue exposure lexicographically; then minimise the SAME financial cost components used to evaluate both rules. There is no arbitrary big monetary penalty. Only the first action is executed. Finite-horizon and forecast approximations remain: it is not a proof of partially observed global optimality.

Both families have nine tuning candidates: horizons 3/5/10 and component quantiles .5/.9/.99. Tuning is separate from cash selection and testing. Locked rules are {"rule": {"kind": "rule", "horizon": 5, "quantile": 0.99, "order": "liquid_first"}, "mpc": {"kind": "mpc", "horizon": 3, "quantile": 0.99, "order": "liquid_first"}}. Every other resource, liability priority, settlement convention and execution cost is shared. Both forward families use effective horizon max(tuned horizon, settlement lag+1), truncated at the experiment end; the myopic diagnostic is exempt. Final review found and corrected a horizon shorter than the lag in the five-day settlement sensitivity. Only that affected stress was refreshed; primary lag2/horizons3 and5 are unchanged. Original development output is retained in work.

[FIGURE:figures/information_and_cash.png]

## 6. Training, risk screen and untouched evaluation

Tuning has 250 paths, training 1000, test 3000; final seeds are 202610410, 202610411, 202610412. A development amendment corrected the omission of timing uncertainty before these final training/test comparisons; the amendment and fresh seeds are recorded. Test paths never choose cash or controller parameters.

The cash grid includes zero, small operating buffers, the source cash reference, and the physical all-cash endpoint. A candidate must have simultaneous one-sided Clopper-Pearson training upper failure bound <=1%, protecting the full cash-policy family. Among passing candidates choose minimum training mean financial cost. If none pass, report infeasible. This is a model-conditional statistical screen, not a real insurer guarantee. Failure tolerance is 1e-5 normalised units, or 1e-7 of the initial total pool. This is a numerical tolerance, not an estimated legal materiality threshold.

Common-cash outcomes isolate recourse. Selected-cash outcomes mix cash design and recourse and are labelled accordingly.

| Common-cash policy | Cash | Failure % | 95% upper % | Mean financial cost |
| --- | --- | --- | --- | --- |
| rule | 2 | 0.16667 | 0.35011 | 0.017809 |
| mpc | 2 | 5.0333 | 5.7399 | 0.015361 |

| Design | Rule minus MPC pp | 95% low | 95% high | Holm p | Rule minus MPC cost |
| --- | --- | --- | --- | --- | --- |
| common_cash2 | -4.8667 | -5.6667 | -4.1333 | 4.4842e-44 | 0.0024485 |
| training_selected | -0.23333 | -0.43333 | -0.066667 | 0.015625 | 9.8762e-05 |

Exact paired discordance tests and Holm adjustment cover the two primary reliability contrasts. Paired bootstrap cost intervals are released. Lower cost with worse safety is NOT called efficiency. Zero-discordance bootstrap intervals are not equivalence or proof of no real risk. Model/parameter error is not covered by these Monte Carlo intervals.

[FIGURE:figures/policy_cost_risk.png]

## 7. Robustness, model risk and continuation

The robustness table varies settlement, yield spread, sale capacity, assumed funding, restrictions, reporting noise/bias and external AU timing at the SAME cash 2, without retuning. Higher-known-severity and separately HIDDEN prior drift are distinguished. The latter generates losses from median 60 while the controller retains the median-30 prior. Forecast/report coverage is conditional on a synthetic observation process, not empirical insurance claim calibration.

| Policy | Horizon | Component q | Window coverage | Cluster 95% low | Cluster 95% high |
| --- | --- | --- | --- | --- | --- |
| rule | 5 | 0.99 | 0.99927 | 0.99854 | 0.99979 |
| mpc | 3 | 0.99 | 0.99891 | 0.99823 | 0.99948 |

The following adverse checks are descriptive and use common cash 2; no post-stress retuning is allowed. Hidden severity drift keeps the controller prior unchanged. The income test distinguishes accrued returns from spendable cash, while the untradeable bucket test removes an assumed source of liquidity.

| Hidden-prior policy | Failure % | 95% upper % | Cost |
| --- | --- | --- | --- |
| rule | 0 | 0.99361 | 0.025822 |
| mpc | 10 | 13.319 | 0.022125 |

| Availability scenario | Policy | Failure % | Cost |
| --- | --- | --- | --- |
| income_accrued_not_available | rule | 0.33333 | 0.018216 |
| income_accrued_not_available | mpc | 5 | 0.015704 |
| less_bucket_untradeable | rule | 0.33333 | 0.017742 |
| less_bucket_untradeable | mpc | 5 | 0.015299 |
| liquid_capacity_double | rule | 0.33333 | 0.017763 |
| liquid_capacity_double | mpc | 5 | 0.01531 |

| True timing concentration | Policy | Failure % | Cost |
| --- | --- | --- | --- |
| 45 | rule | 11.667 | 0.018421 |
| 45 | mpc | 46 | 0.016035 |
| 720 | rule | 0 | 0.01741 |
| 720 | mpc | 0 | 0.014997 |

Untuned myopic and five-day/q90 rules are descriptive checks only. The main tuned base-stock family remains the primary strong comparator.

| Fixed rule at cash 2 | Failure % | Cost |
| --- | --- | --- |
| fixed_myopic | 100 | 0.012887 |
| fixed_buffer5_q90 | 5.6667 | 0.015454 |

| Known sensitivity | Policy | Failure % | Cost |
| --- | --- | --- | --- |
| settlement_0 | rule | 0 | 0.016633 |
| settlement_0 | mpc | 1.3333 | 0.010409 |
| settlement_1 | rule | 0 | 0.016633 |
| settlement_1 | mpc | 10.333 | 0.012831 |
| yield_spread_0.5pp | rule | 0 | 0.010811 |
| yield_spread_0.5pp | mpc | 6.6667 | 0.0095603 |
| yield_spread_2pp | rule | 0 | 0.029578 |
| yield_spread_2pp | mpc | 6.6667 | 0.025152 |
| capacity_half | rule | 0 | 0.01912 |
| capacity_half | mpc | 6.6667 | 0.016579 |
| hypothetical_facility3 | rule | 0 | 0.019721 |
| hypothetical_facility3 | mpc | 0.33333 | 0.01701 |
| cash_fungible | rule | 0 | 0.013625 |
| cash_fungible | mpc | 6.6667 | 0.011148 |
| report_bias_down30logpct | rule | 1 | 0.016772 |
| report_bias_down30logpct | mpc | 15.667 | 0.014697 |
| report_noise_high | rule | 0 | 0.019069 |
| report_noise_high | mpc | 5 | 0.016256 |
| au_flood_timing | rule | 0.66667 | 0.018684 |
| au_flood_timing | mpc | 6 | 0.016001 |
| settlement_5 | rule | 1.3333 | 0.023507 |
| settlement_5 | mpc | 1.3333 | 0.023456 |

Average forecast-window coverage must not be confused with the probability of no breach over the entire path. A whole-path all-prefix diagnostic is:

| Policy | Mean prefix-window coverage | Paths any prefix breach % | 95% upper % |
| --- | --- | --- | --- |
| rule | 0.99734 | 8.6667 | 11.822 |
| mpc | 0.99797 | 8.3333 | 11.445 |

Mechanically selected first discordant paths are replayed in discordant_failure_diagnostics.csv. They are descriptive post-test diagnosis, not independent confirmation. They compare the forecast available on the last settlement decision date with the later actual demand. Timing surprises can cause failure even without an intervening ultimate-report revision; the control risk is not captured by average posterior coverage alone.

| Design | Path | Failure day | Earlier day forecast | Actual day demand | First arrears |
| --- | --- | --- | --- | --- | --- |
| common_cash2 | 2 | 43 | 0.61705 | 1.167 | 0.027824 |
| training_selected | 420 | 55 | 0.80685 | 2.5452 | 0.20057 |

A separate 52-week path family has exact primary/continuation prefixes, no new draws after day 65, and all residual obligations retained. It is not ultimate runoff closure and includes no additional catastrophe/new underwriting loss.

| Policy | Core13 failure % | Full52 failure % | Terminal TP | Terminal debt | Terminal arrears |
| --- | --- | --- | --- | --- | --- |
| rule | 0 | 1 | 10.327 | 0 | 0 |
| mpc | 3.3333 | 12.667 | 10.327 | 0 | 0 |

## 8. Same-model exact benchmark and verification

Unlike v3's separate toy economics, 12 deterministic full-horizon LP cases are replayed in the ACTUAL v4 engine with identical cost components and settlement. Cash plan/replay maximum discrepancy is 9.99e-16; financial-objective discrepancy after known constants is 2.6e-18. They are explicitly perfect-information cases for verification. Their information advantage is not given to deployable rules, and this is not a global partially observed optimality certificate. Test policy parameters are not chosen by these cases.

A guarded three-day/no-facility analytic action accelerates a special case of the original LP. On 120 fixed random-state checks, its largest first-action discrepancy is below 1e-6. This is a local solver equivalence check, not a global partial-information optimality certificate. Economic endpoint checks include positive, zero and negative yield spreads: cash can rationally dominate when its yield is higher; the study does not force an interior solution.

The current suite records 58 passing tests, covering source cash bridges, restricted balances, unsettled proceeds, independent returns/cash/P&L, late cohorts, optional funding, immutable observations, prefix invariance, report-only posterior arithmetic, timing envelopes and exact replay. The public verification command writes a local test log and checks the retained results. This is software/method verification, not independent professional sign-off.

## 9. Practical use and limitations

The useful output is a decision/validation workflow: identify usable cash, pending settlements and obligations; separate reliability from cost; compare complexity with a strong rule; and report sensitivity before recommending a buffer. Application would require deadline-level liabilities, executable trading constraints and contractual funding terms. Public data now inform important scope and constraint choices, but do not validate private due dates, actual caps/spreads, a signed loan line, report noise or catastrophe severities.

Full asset/FX/default risk, complete premium/expense flows, reserve estimation uncertainty calibrated to a real book, legal priorities, counterparty collectibility and ultimate runoff remain open. A model can be carefully implemented and still inappropriate for an operational decision. Actual independent actuarial/treasury review is outstanding.

## Professional context

IAIS's 2020 Application Paper on Liquidity Risk Management informs the challenge themes: governance, entity/location restrictions, stress analysis, usable assets and contingency funding. It is guidance rather than a new binding standard. PRA SS5/19 (November 2024) is UK supervisory context; it is not asserted to govern this NZ/Australia case. This scoped engine omits important full-company exposures and cannot establish compliance. The source register records the references; exact historical copies can be obtained locally with the source-retrieval helper.

## Primary references and provenance

Tower Limited Annual Report 2025 (printed pp.43,45,62,68,80): https://www.tower.co.nz/wp-content/uploads/2025/11/FINAL-FY25-TWR-Annual-Report.pdf . NZX settlement context: https://www.nzx.com/services/nzx-clearing/about .

ICNZ Kaikoura paid table: https://www.icnz.org.nz/industry/media-releases/private-insurers-paid-out-0-5-billion-kaikoura-earthquake-claims/ ; lower-bound update: https://www.icnz.org.nz/industry/media-releases/settlements-reached-for-82-of-kaikoura-claims/ ; historical nominal reference: https://www.icnz.org.nz/industry/cost-of-natural-disasters/ .

ICA 2022 updates: https://insurancecouncil.com.au/resource/updated-data-shows-2022-flood-was-australias-costliest/ ; https://insurancecouncil.com.au/resource/2022-flood-now-third-costliest-natural-disaster-ever/ ; https://insurancecouncil.com.au/resource/2-billion-in-flood-payments-already-made-by-insurers/ ; https://insurancecouncil.com.au/resource/three-year-weather-bill-reaches-12-3-billion/ .

IAIS guidance: https://www.iais.org/uploads/2022/01/200629-Application-Paper-on-Liquidity-Risk-Management.pdf . PRA context: https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2024/ss519-november-2024-update.pdf .

Exact NZ2023 row URLs, all retrieval hashes, source measurement limits and conversion choices are in SOURCE_REGISTER.md and data/. Prior ALM/price-impact literature and v3 originality limitations remain relevant; v4 does not claim first-in-literature status. Sources checked 14 October 2026.
