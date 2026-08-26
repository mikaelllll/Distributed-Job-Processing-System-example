# Benchmarking model

Dispatch generates controlled internal work to demonstrate distributed execution. It does not make thousands of browser requests or target an external website.

## Execution modes

| Mode | Purpose |
| --- | --- |
| Audit | Smaller, inspectable runs focused on behavior and correctness |
| Benchmark | Real jobs used to measure queueing, processing, retries, latency, and throughput |
| Simulation | Aggregated modelling for extreme scales that would be unsuitable for a free Codespace |

The 100-million-job option is always presented as simulation. It represents the expected accounting and visualization shape without publishing 100 million RabbitMQ messages.

## Workloads

Workload profiles model different processing characteristics. Duration, failure probability, retry limit, producer concurrency, and target rate can be adjusted within validated boundaries. Contextual help in the interface explains the impact of each option.

A configured failure probability creates retry and permanent-failure behavior intentionally. A completed run can therefore show fewer successful jobs than requested while still accounting for every job through permanent failures.

## Accounting invariants

A terminal real run must satisfy:

```text
succeeded + permanently_failed = requested
pending = running = awaiting_retry = 0
```

Retries are attempts, not additional requested jobs. The dashboard keeps successful completion, permanent errors, retry attempts, executing work, and awaiting-retry work separate to avoid misleading totals.

## Throughput and latency

Throughput is derived from work completed over time, not from the current cumulative total divided repeatedly after completion. Latency percentiles summarize observed end-to-end job time. Final metrics are persisted so reopening a report does not restart collection.

## Responsible use

Real runs are limited to one million jobs by default. Raising this limit can produce substantial broker traffic, CPU use, memory pressure, database writes, network activity, and cost. Only benchmark systems you own or have explicit permission to test.
