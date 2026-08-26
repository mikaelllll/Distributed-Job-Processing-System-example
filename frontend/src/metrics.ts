import type { Metrics, RunMode } from './types'

export const compact = new Intl.NumberFormat('en', {
  notation: 'compact',
  maximumFractionDigits: 1,
})
export const number = new Intl.NumberFormat('en')

export function modeForJobCount(jobCount: number, currentMode: RunMode): RunMode {
  if (jobCount > 1_000_000) return 'simulation'
  return currentMode === 'simulation' ? 'benchmark' : currentMode
}

export function detectBottleneck(
  metrics: Metrics,
): { title: string; detail: string; severity: string } {
  const queued = metrics.queued ?? 0
  const running = metrics.running ?? 0
  const workers = metrics.active_workers ?? 0
  const retries = metrics.retries ?? 0
  const completed = metrics.completed ?? 0
  if (workers === 0 && queued > 0) {
    return {
      title: 'No worker capacity',
      detail: 'Jobs are queued, but no active workers are reporting heartbeats.',
      severity: 'danger',
    }
  }
  if (queued > Math.max(1000, completed * 0.25) && running > 0) {
    return {
      title: 'Worker capacity constrained',
      detail: 'Queue growth is outpacing job completion. Add workers or reduce the submission rate.',
      severity: 'warning',
    }
  }
  if (retries > Math.max(10, completed * 0.05)) {
    return {
      title: 'Elevated retry rate',
      detail: 'More than 5% of processed jobs required retries. Inspect the workload or dependency.',
      severity: 'warning',
    }
  }
  return {
    title: 'No clear bottleneck',
    detail: 'Submission and processing rates currently appear balanced.',
    severity: 'healthy',
  }
}

export function mergeMetricHistory(persisted: Metrics[], live: Metrics[], limit = 180): Metrics[] {
  const samples = new Map<string, Metrics>()
  for (const sample of [...persisted, ...live]) {
    if (sample.timestamp) samples.set(sample.timestamp, sample)
  }
  return [...samples.values()]
    .sort((left, right) => Date.parse(left.timestamp!) - Date.parse(right.timestamp!))
    .slice(-limit)
}
