# Project summary: catastrophe claims and liquidity management

The study asks when a liquidity controller should sell assets to meet catastrophe claims whose ultimate size and payment timing are only partially observed. Restricted cash and unsettled sale proceeds are kept separate from cash available for payment.

## Results

At the same initial cash allocation of 2 per 100 pool units, a tuned base-stock rule missed payments in 5 of 3,000 held-out simulations, compared with 151 for MPC. At training-selected cash of 20, the counts were 0 and 7. Both selected designs had one-sided test upper failure bounds below the declared 1% target. MPC's slightly lower financial cost came with lower reliability.

The cash-20 result is a selection on the declared grid, not a continuous optimum. Several lower-cash rule candidates narrowly missed the simultaneous training confidence screen. Timing misspecification materially worsens both policies.

## Model and evidence

- A daily ledger tracks accessible and restricted cash, two asset buckets, pending trades, claims arrears, recovery assets and optional secured debt. Cash-flow and own-funds identities are checked each day.
- Both controllers receive the same current observations, dated receipts and report-based forecasts. Hidden ultimate losses and future actual payments are reserved for validation.
- Separate cohorts cover policy tuning (250 paths), cash selection (1,000) and testing (3,000). Paired comparisons, deterministic LP replays and stresses assess the results.
- Public disclosures supply financial anchors and 11 disaster-payment snapshots across three related-event groups. Daily payment allocation, loss/report uncertainty, trading capacity and recovery timing remain model assumptions.

## Reproduction and limitations

Run `python verify_public.py` to check the published model and results. The optional `--with-sources` mode also requires the historical source cache and audits 40 company values and two event-table amounts. The [README](README.md) describes both modes.

The framework covers a closed-book liquidity pool. It does not reconstruct a complete insurer balance sheet, regulatory capital requirement or contractual payment calendar. Company use would require deadline-level cash flows, security-level trading and settlement data, and actual funding and reinsurance terms.
