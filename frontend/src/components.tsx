import type { ReactNode } from 'react'
import { Workflow } from 'lucide-react'
import type { RunStatus } from './types'

export function HelpTip({ label, children }: { label: string; children: ReactNode }) {
  return <span className="help-tip" tabIndex={0} role="button" aria-label={`Help: ${label}`}><span aria-hidden="true">?</span><span className="help-panel" role="tooltip"><strong>{label}</strong>{children}</span></span>
}

export function FieldLabel({ children, help }: { children: ReactNode; help: ReactNode }) {
  return <span className="field-title">{children}<HelpTip label={String(children)}>{help}</HelpTip></span>
}

export function MetricCard({ label, value, detail, tone = 'blue', help }: { label: string; value: ReactNode; detail?: string; tone?: string; help?: ReactNode }) {
  return <article className={`metric-card tone-${tone}`}><span className="metric-label">{label}{help && <HelpTip label={label}>{help}</HelpTip>}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</article>
}

export function StatusBadge({ status }: { status: RunStatus }) {
  return <span className={`status status-${status}`}><i />{status}</span>
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty"><Workflow size={34} /><p>{children}</p></div>
}
