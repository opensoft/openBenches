# Tasks

| Set | Outcome | Task IDs | Predecessor | Verification | Safe intermediate state |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Durable repository adoption | T001-T003 | main with PR 326 | Source adoption audit, existing delivery tests and clean Git export | Assets and pointers land together; no runtime or queue changes |

- [x] T001 Track the unchanged shared skill in both discovery homes and add repository pointers; active-plan block and existing templates match the base.
- [x] T002 Add source adoption/negative/preservation tests and ordinary CI coverage; six adoption, 12 delivery and nine five-job parity tests passed.
- [x] T003 Validate skill/OpenSpec/whitespace and pass the clean staged Git export audit; publish this artifact as an unqueued 1.7 PR with exact-head review requested. Hosted gates are recorded separately.
