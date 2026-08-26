# Frontend

The frontend is a React and TypeScript single-page application served by Nginx. It is an operational dashboard, not a static demonstration page: configuration controls create real backend runs and the interface follows their lifecycle.

## Main experiences

- Create a benchmark from predefined job counts and configurable workload behavior.
- Understand every configurable field through contextual help tooltips.
- Compare audit, benchmark, and extreme-scale simulation modes.
- Follow live counters and charts while a run is active.
- Inspect final throughput, latency, errors, distribution, and bottleneck diagnosis.
- Browse run history, reopen completed reports, cancel work, and delete runs.

## Data flow

TanStack Query manages request state and durable API data. Server-Sent Events deliver live metric snapshots for the selected run. Historical samples are merged chronologically and deduplicated before they reach Recharts.

Collection ends when the backend reports a terminal run. This preserves the meaningful execution window and prevents completed charts from turning into long flat lines.

## Charts

The dashboard separates cumulative and rate-based measurements:

- **Queue and completion** shows work moving through the system.
- **Processing throughput** shows completed jobs per second.
- **Latency percentiles** shows P50, P95, and P99 end-to-end latency.
- **Worker and error statistics** expose concurrency, retries, and permanent failures.
- **Automated diagnosis** summarizes evidence that suggests queue, processing, or capacity pressure.

Simulation runs can complete in very few snapshots. Charts therefore support single-point results without inventing fake intermediate measurements.

## Quality

The frontend uses strict TypeScript, ESLint, Vitest, production Vite builds, reusable metric utilities, accessible labels, and responsive layout rules. Nginx supplies security headers and routes API traffic to the backend within the Compose network.
