# V4 mathematical specification and units

This specification describes the implemented closed-book liquidity pool, not an insurer valuation or a globally optimal partially observed policy.

## Perimeter and clock

Initial total financial assets are 100 normalised units, including restricted cash R. Decision cash c is accessible: 0 <= c <= 100-R. Remaining assets are split into assumed execution buckets G and B. A unit is 1% of the defined pool, not 1% of the insurer's total assets or regulatory capital. There are 260 business days per model year. Numerical late-payment tolerance is 1e-5 units.

Primary horizon T=65; continuation T=260. Each scenario is conditional on one catastrophe at inception. Existing incurred liabilities run off; new premiums, expenses, new underwriting and additional events are excluded. Constant investment marks deliberately omit duration/credit/FX risk. No inference about full-firm solvency adequacy follows.

## Intraday ordering and conservation

Opening inventories are measured before trading. Dated settlement receipts and collected reinsurance arrive first. Model income is accrued and, in the base approximation, credited. The no-income-cash stress credits a separate inaccessible receivable instead. Loan interest capitalises. The current report and today's due claims become observable. Then the controller acts, paying previously overdue claims before today's claims, and repays callable/requested debt from remaining accessible cash.

Let xG and xB be gross asset sales, hG and hB dealing fractions, d the lag and n=(1-hG)xG+(1-hB)xB. Sold inventory is removed immediately and n enters the dated queue; when d>0 it cannot pay today's claims. When d=0 it is immediately accessible. Holdings must cover sales and previously pledged lower-cost assets remain encumbered. Daily sale bounds apply. Debt is limited by both the facility and advance times remaining eligible assets. Cancellation of simultaneous gross borrow/repay occurs before actual first-action execution.

Let A be arrears, L today's due claim demand, C accessible cash, Q pending sales, I inaccessible earned income, V nominal remaining claim liability and U remaining ultimate recovery. The engine checks two independent identities each day:

* Accessible cash change = settled sales + collected recovery + spendable income + net borrowing + immediate-sale proceeds - paid claims - principal repaid.
* Own funds = C + restricted cash + unsold holdings + Q + I + U - V - debt. Its independently accumulated change is earned investment income - execution expense - loan interest - inception commitment fee. Paying claims reduces cash and V together; recovery collection reduces U and raises cash together. Neither creates profit on collection.

True V and U are validation states. Controller observations do not contain them. A separate reported-estimate reserve bridge uses the report-based loss estimate and tracks estimate revisions explicitly; it is not IFRS measurement.

## Economic objective

For each day, using balances after settlements but before daily accrual/trading, let a be the assumed annual investment accrual rate, r the cash rate and delta=a-r. The financial cost is:

J = sum_t [(C_t + R_t)*delta/260 + pending_t*a/260 + hG*xG_t + hB*xB_t + debt_open_t*funding_rate/260] + facility*commitment_rate*T/260.

Pending sales are assumed not to earn income. Delta is opportunity cost, not a cash outflow, and is not debited again from the cash ledger. Gross claim payments and principal repayment are not expenses in J. No capital/shortfall penalty is included. Restricted-cash drag is retained as a largely common term. The rate proxy is not an identified expected marginal risk premium. With delta<0, cash can be economically preferable; no interior optimum is imposed.

The design problem is to minimise simulated E[J(c,policy)] over the declared cash grid and locked policy families subject to P(any material overdue claim or unpaid callable debt during T | catastrophe at inception) <= 1%. Training uses a conservative simultaneous upper confidence screen, rather than asserting the unknown probability is known. The 1% appetite is a research setting, not a legal/management-approved limit.

## Hidden event and information

Ultimate catastrophe loss Z has a synthetic lognormal prior, log Z ~ Normal(mu0,v0). Every fifth business day an observed log report y=log Z+epsilon is generated with independent Normal(0,sigma^2) noise. The report-only update is v_new=(1/v_old+1/sigma^2)^(-1), mu_new=v_new*(mu_old/v_old+y/sigma^2). Hidden-bias stress violates that observation model.

Noisy ultimate reporting is not calibrated from the public aggregate payment snapshots. Paid/announced catastrophe demands are a hard lower bound for forecast ultimate, but are not fully assimilated into the Gaussian posterior. The released 90% posterior interval therefore has a report-only interpretation, not a full-information actuarial confidence interval.

Mean payment CDF F(t) is a fitted Weibull on event-relative weeks. A full 260-business-day allocation plus tail is drawn from Dirichlet(kappa*w), where w are increments of F; kappa is assumed. This represents synthetic due-payment concentration, not observed legal deadlines. Conditional remaining cumulative fractions use Beta marginals. The selected loss quantile multiplied by cumulative timing-envelope increments is a deterministic risk scenario. It is not an exact joint quantile or calibrated full predictive distribution. Receding envelopes can be time inconsistent.

Both controllers see immutable current cash/inventory/debt, dated pending receipts, arrears, today's demand, report-based belief, known cumulative demands and the same forecast vector. They do not see true Z, future actual payments or uncollected recovery. Conservative recovery forecasting counts no future collection before receipt. This is partial information but not an optimal POMDP solver.

## Decision families and benchmark

The simple family is a forecast base-stock rule with conservative spendable income: cover the largest cumulative net demand in its horizon, then sell lower-cost assets first within caps. Both families tune horizons 3/5/10 and component quantiles .5/.9/.99 on a separate tuning cohort. Sale order is fixed for both. Effective forecast horizon is max(tuned horizon, settlement lag+1), truncated at the experiment end. A deliberately myopic diagnostic is exempt. This execution guard was added after final stress review and changes the lag5 sensitivity, not primary lag2/horizons3 and5.

MPC plans dated cash, inventory, borrowing, payment and arrears over the finite forecast horizon. Stage one minimises forecast arrears exposure lexicographically; stage two minimises the same financial cost components over its lookahead, with an explicit residual-debt charge/terminal obligation. Stage-one exposure is an inner safety proxy, not exactly the outer failure-probability constraint. Only the first action executes. There is no claim of global optimisation of E[J] under the outer reliability constraint.

The deterministic exact benchmark supplies realised future payments to an LP for software verification and replays its plan in the same engine. It has an information advantage and is not a deployable comparator. A guarded H<=3/no-facility special case uses an analytic first action, checked against the original two-stage LP; this is a local numerical equivalence claim only.

## Selection and uncertainty

Tuning, cash-training and test cohorts use independent seed groups. For M=26 candidate cash-policy pairs, each training upper bound is Clopper-Pearson at alpha=0.05/M. If k=0 of n, upper=1-alpha^(1/n); otherwise the beta quantile is used. The familywise protection is conditional on the simulation model and independent tuning. Minimum mean training cost among candidates passing the 1% upper-bound screen is selected. No feasible candidate means infeasible; the test is never used to rescue selection.

Test reports one-sided exact 95% failure upper bounds for each locked design. Two primary paired failure contrasts use exact discordance tests with Holm correction, plus paired path bootstrap descriptive intervals; cost contrasts also use paired bootstrap. Bootstrap degeneracy is not proof of equivalence or zero risk. Forecast coverage intervals resample paths, not correlated daily windows. Robustness and transfer checks are exploratory. Monte Carlo intervals do not cover parameter, perimeter, public-data measurement or structural model error.
