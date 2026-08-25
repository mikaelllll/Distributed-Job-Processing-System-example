export type RunStatus = 'pending' | 'producing' | 'running' | 'completed' | 'cancelled' | 'failed'
export type RunMode = 'audit' | 'benchmark' | 'simulation'

export interface Run {
  id: string
  name: string
  status: RunStatus
  mode: RunMode
  job_count: number
  producer_concurrency: number
  target_rate: number | null
  workload: string
  duration_ms: number
  failure_probability: number
  max_retries: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  final_metrics: Metrics | null
  snapshots?: Array<Metrics & { recorded_at: string }>
}

export interface Metrics {
  timestamp?: string
  requested?: number
  submitted?: number
  queued?: number
  running?: number
  completed?: number
  failed?: number
  retrying?: number
  retries?: number
  dead_lettered?: number
  active_workers?: number
  elapsed_seconds?: number
  throughput?: number
  average_processing_ms?: number
  average_queue_ms?: number
  p50_ms?: number
  p95_ms?: number
  p99_ms?: number
}

export interface RunCreate {
  name: string
  job_count: number
  mode: RunMode
  producer_concurrency: number
  target_rate: number | null
  workload: string
  duration_ms: number
  failure_probability: number
  max_retries: number
}

