import type { ReactNode } from 'react'
import { Activity, AlertTriangle, CheckCircle2, Clock3, Server, Workflow } from 'lucide-react'
import type { Metrics, RunStatus } from './types'

export function MetricCard({ label, value, detail, tone = 'blue' }: { label: string; value: ReactNode; detail?: string; tone?: string }) {
  return <article className={`metric-card tone-${tone}`}><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</article>
}

export function StatusBadge({ status }: { status: RunStatus }) {
  return <span className={`status status-${status}`}><i />{status}</span>
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty"><Workflow size={34} /><p>{children}</p></div>
}

export const icons = { Activity, AlertTriangle, CheckCircle2, Clock3, Server }

export function detectBottleneck(metrics: Metrics): { title: string; detail: string; severity: string } {
  const queued = metrics.queued ?? 0
  const running = metrics.running ?? 0
  const workers = metrics.active_workers ?? 0
  const retries = metrics.retries ?? 0
  const completed = metrics.completed ?? 0
  if (workers === 0 && queued > 0) return { title: 'No worker capacity', detail: 'Jobs are queued, but no active workers are reporting heartbeats.', severity: 'danger' }
  if (queued > Math.max(1000, completed * 0.25) && running > 0) return { title: 'Worker capacity constrained', detail: 'Queue growth is outpacing job completion. Add workers or reduce the submission rate.', severity: 'warning' }
  if (retries > Math.max(10, completed * 0.05)) return { title: 'Elevated retry rate', detail: 'More than 5% of processed jobs required retries. Inspect the workload or dependency.', severity: 'warning' }
  return { title: 'No clear bottleneck', detail: 'Submission and processing rates currently appear balanced.', severity: 'healthy' }
}

export const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
export const number = new Intl.NumberFormat('en')

