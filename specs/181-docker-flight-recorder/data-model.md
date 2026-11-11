# Evidence model

Version 1 samples: UTC timestamp, fixed phase label, collector PID/start time, independent probe outcomes/latencies, Windows resources, selected-container identity/state, rotated bench accounting, task state/results, watchdog freshness, polling window counts and explicit issue codes. Missing fields are unavailable, not zero or healthy.

Outcomes: success, exit-error, timeout, exception, circuit-open, unavailable. Timeouts and interrupted in-flight probes persist a circuit latch across process replacement until explicit ResetProbes while stopped. Status is stopped if process identity is absent, stale beyond three intervals, otherwise reflects issues. Phase start times and log-window freshness prevent old polling tails being presented as new-phase activity.

Host-local storage: status.json, samples.jsonl plus three rotations, phase.json, at most twelve incident summaries. Fixed labels: baseline, dashboard-open, dashboard-closed, dashboard-reopened. No arbitrary free text.
