import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, ArrowRight, BarChart3, Boxes, Gauge, Github, Play, Radio, Square, Trash2 } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Link, NavLink, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { api } from './api'
import { EmptyState, FieldLabel, HelpTip, MetricCard, StatusBadge } from './components'
import { useRunMetrics } from './hooks'
import { compact, detectBottleneck, mergeMetricHistory, modeForJobCount, number } from './metrics'
import type { Metrics, RunCreate } from './types'

function Shell() {
  return <div className="shell">
    <header><Link className="brand" to="/"><span><Boxes size={21} /></span><div>DISPATCH<small>JOB OBSERVATORY</small></div></Link>
      <nav><NavLink to="/">Overview</NavLink><NavLink to="/new">New benchmark</NavLink></nav>
      <a className="github" href="https://github.com/mikaelllll/Distributed-Job-Processing-System-example" target="_blank" rel="noreferrer"><Github size={18} /> Source</a>
    </header>
    <main><Routes><Route path="/" element={<Overview />} /><Route path="/new" element={<CreateRun />} /><Route path="/runs/:id" element={<RunView />} /></Routes></main>
    <footer>Built to make distributed systems observable. <span>FastAPI · RabbitMQ · Redis · PostgreSQL · React</span></footer>
  </div>
}

function Overview() {
  const client = useQueryClient()
  const { data: runs = [], isLoading } = useQuery({ queryKey: ['runs'], queryFn: api.listRuns, refetchInterval: 5000 })
  const remove = useMutation({ mutationFn: api.deleteRun, onSuccess: () => client.invalidateQueries({ queryKey: ['runs'] }) })
  const active = runs.filter((run) => ['pending', 'producing', 'running'].includes(run.status))
  const completed = runs.filter((run) => run.status === 'completed')
  return <>
    <section className="hero"><div><span className="eyebrow"><Radio size={14} /> Distributed systems, made visible</span><h1>Watch work move.<br/><em>Find what slows it down.</em></h1><p>Generate controlled workloads, distribute them across asynchronous workers, and inspect throughput, latency, failures, and bottlenecks as they happen.</p><div className="hero-actions"><Link className="button primary" to="/new"><Play size={17} /> Run a benchmark</Link><a className="button ghost" href="#runs">View history <ArrowRight size={17} /></a></div></div><div className="system-map"><div className="map-node client">LOAD GENERATOR</div><ArrowRight/><div className="map-node broker">RABBITMQ<small>durable queue</small></div><div className="worker-row"><div>W1</div><div>W2</div><div>W3</div></div><div className="map-stats"><span><i className="green"/> AT-LEAST-ONCE</span><span><i/> LIVE METRICS</span></div></div></section>
    <section className="summary-grid"><MetricCard label="Total runs" value={runs.length} detail="Recorded benchmarks"/><MetricCard label="Active now" value={active.length} detail="Producing or processing" tone="green"/><MetricCard label="Completed" value={completed.length} detail="Final reports available" tone="purple"/><MetricCard label="Largest run" value={compact.format(Math.max(0, ...runs.map(r => r.job_count)))} detail="Logical jobs" tone="orange"/></section>
    <section id="runs" className="panel"><div className="section-heading"><div><span className="eyebrow">Benchmark history</span><h2>Recent runs</h2></div><Link className="button small" to="/new">New run</Link></div>
      {isLoading ? <div className="empty">Loading runs…</div> : runs.length === 0 ? <EmptyState>No benchmarks yet. Create the first workload to see the system in action.</EmptyState> : <div className="table-wrap"><table><thead><tr><th>Run</th><th>Status</th><th>Mode</th><th>Jobs</th><th>Workload</th><th>Created</th><th/></tr></thead><tbody>{runs.map(run => <tr key={run.id}><td><strong>{run.name}</strong><small>{run.id.slice(0, 8)}</small></td><td><StatusBadge status={run.status}/></td><td>{run.mode}</td><td>{number.format(run.job_count)}</td><td>{run.workload.replace('_', ' ')}</td><td>{new Date(run.created_at).toLocaleString()}</td><td><div className="row-actions"><Link to={`/runs/${run.id}`}>Inspect <ArrowRight size={14}/></Link><button className="delete-run" aria-label={`Delete ${run.name}`} title="Stop and delete run" disabled={remove.isPending} onClick={() => { if (window.confirm(`Stop and permanently delete “${run.name}”?`)) remove.mutate(run.id) }}><Trash2 size={16}/></button></div></td></tr>)}</tbody></table></div>}
    </section>
  </>
}

function CreateRun() {
  const navigate = useNavigate()
  const [form, setForm] = useState<RunCreate>({ name: 'Throughput benchmark', job_count: 10_000, mode: 'benchmark', producer_concurrency: 20, target_rate: 5000, workload: 'io_light', duration_ms: 25, failure_probability: 0.01, max_retries: 3 })
  const mutation = useMutation({ mutationFn: api.createRun, onSuccess: run => navigate(`/runs/${run.id}`) })
  const update = (key: keyof RunCreate, value: string | number | null) => setForm(current => ({ ...current, [key]: value }))
  const updateJobCount = (value: number) => setForm(current => ({
    ...current,
    job_count: value,
    mode: modeForJobCount(value, current.mode),
  }))
  const submit = (event: FormEvent) => { event.preventDefault(); mutation.mutate(form) }
  return <section className="create-layout"><div className="page-title"><span className="eyebrow">Controlled experiment</span><h1>Configure benchmark</h1><p>Create a reproducible workload. The browser sends one command; the dedicated generator publishes jobs at the configured rate.</p></div><form className="config-panel" onSubmit={submit}>
    <fieldset><legend>Run identity</legend><label><FieldLabel help="A descriptive name used to identify this experiment in benchmark history.">Benchmark name</FieldLabel><input value={form.name} onChange={e => update('name', e.target.value)} required maxLength={120}/></label></fieldset>
    <fieldset><legend>Scale</legend><label><FieldLabel help="The total number of logical jobs requested. Up to one million are published as real RabbitMQ messages; larger presets use simulation mode.">Number of logical jobs</FieldLabel><div className="presets">{[10_000,100_000,1_000_000,100_000_000].map(value => <button type="button" className={form.job_count === value ? 'selected' : ''} onClick={() => updateJobCount(value)} key={value}>{compact.format(value)}</button>)}</div><input type="number" min="1" max="100000000" value={form.job_count} onChange={e => updateJobCount(Number(e.target.value))}/></label><div className="form-grid"><label><FieldLabel help={<><b>Audit:</b> detailed, lower-volume validation.<br/><b>Benchmark:</b> real RabbitMQ jobs processed by workers.<br/><b>Simulation:</b> modeled results above one million jobs; workload code is not executed.</>}>Execution mode</FieldLabel><select value={form.mode} onChange={e => update('mode', e.target.value)}><option value="audit">Audit — detailed</option><option value="benchmark">Benchmark — real jobs</option><option value="simulation" disabled={form.job_count <= 1_000_000}>Simulation — above 1M only</option></select></label><label><FieldLabel help="Maximum number of job publications the producer may have in flight concurrently. Higher values can increase broker submission throughput.">Producer concurrency</FieldLabel><input type="number" min="1" max="500" value={form.producer_concurrency} onChange={e => update('producer_concurrency', Number(e.target.value))}/></label><label><FieldLabel help="Desired publication rate. The generator throttles message submission toward this number; workers may process at a different rate.">Target jobs / second</FieldLabel><input type="number" min="1" value={form.target_rate ?? ''} onChange={e => update('target_rate', e.target.value ? Number(e.target.value) : null)}/></label></div></fieldset>
    <fieldset><legend>Workload behavior</legend><div className="form-grid"><label><FieldLabel help={<><b>Light I/O:</b> short asynchronous dependency wait.<br/><b>Heavy I/O:</b> sustained asynchronous dependency work.<br/><b>Light CPU:</b> hashing work performed off the event loop.<br/><b>Unreliable dependency:</b> I/O work with configurable injected failures.</>}>Workload</FieldLabel><select value={form.workload} onChange={e => update('workload', e.target.value)}><option value="io_light">Light I/O</option><option value="io_heavy">Heavy I/O</option><option value="cpu_light">Light CPU</option><option value="unreliable">Unreliable dependency</option></select></label><label><FieldLabel help="Approximate processing time added to each job. Increasing it reduces each worker's capacity and can create queue pressure.">Duration per job (ms)</FieldLabel><input type="number" min="0" max="60000" value={form.duration_ms} onChange={e => update('duration_ms', Number(e.target.value))}/></label><label><FieldLabel help="Independent chance that each processing attempt fails. Failed attempts are retried until the configured limit is reached.">Failure probability (%)</FieldLabel><input type="number" min="0" max="100" step="0.1" value={form.failure_probability * 100} onChange={e => update('failure_probability', Number(e.target.value) / 100)}/></label><label><FieldLabel help="Number of delayed attempts allowed after an initial failure. Jobs that exhaust this limit enter the dead-letter queue.">Maximum retries</FieldLabel><input type="number" min="0" max="10" value={form.max_retries} onChange={e => update('max_retries', Number(e.target.value))}/></label></div></fieldset>
    {form.job_count > 1_000_000 && <div className="notice">Extreme-scale runs use simulation mode to protect the public deployment and avoid storing millions of individual records.</div>}{mutation.error && <div className="error-box">{mutation.error.message}</div>}<button className="button primary submit" disabled={mutation.isPending}><Play size={18}/>{mutation.isPending ? 'Starting…' : 'Start benchmark'}</button>
  </form></section>
}

function RunView() {
  const { id } = useParams()
  const client = useQueryClient()
  const { data: run, isLoading } = useQuery({ queryKey: ['run', id], queryFn: () => api.getRun(id!), enabled: !!id, refetchInterval: 3000 })
  const isTerminal = !!run && ['completed', 'cancelled', 'failed'].includes(run.status)
  const live = useRunMetrics(id, !isTerminal)
  const cancel = useMutation({ mutationFn: () => api.cancelRun(id!), onSuccess: () => client.invalidateQueries({ queryKey: ['run', id] }) })
  const metrics = useMemo(
    () => Object.keys(live.metrics).length ? live.metrics : (run?.final_metrics ?? {}),
    [live.metrics, run?.final_metrics],
  )
  const chartData = useMemo(
    () => mergeMetricHistory(run?.snapshots ?? [], live.history),
    [run?.snapshots, live.history],
  )
  const bottleneck = useMemo(() => detectBottleneck(metrics), [metrics])
  if (isLoading || !run) return <div className="empty">Loading benchmark…</div>
  const progress = Math.min(100, ((metrics.completed ?? 0) + (metrics.failed ?? 0)) / run.job_count * 100)
  return <><section className="run-header"><div><span className="eyebrow">Benchmark {run.id.slice(0, 8)}</span><h1>{run.name}</h1><div className="run-meta"><StatusBadge status={run.status}/><span>{run.mode}</span><span>{number.format(run.job_count)} jobs</span><span>{run.workload.replace('_',' ')}</span></div></div>{!['completed','cancelled','failed'].includes(run.status) && <button className="button danger" onClick={() => cancel.mutate()}><Square size={15}/> Cancel run</button>}</section>
    <div className="progress"><div style={{width: `${progress}%`}}/><span>{progress.toFixed(1)}%</span></div>
    <section className="summary-grid live"><MetricCard label="Succeeded" value={number.format(metrics.completed ?? 0)} detail={`${number.format(metrics.queued ?? 0)} pending`} tone="green" help="Jobs that completed successfully. Pending includes both ready jobs and jobs waiting in delayed retry queues."/><MetricCard label="Throughput" value={`${compact.format(metrics.throughput ?? 0)}/s`} detail={`${metrics.elapsed_seconds ?? 0}s elapsed`} help="Average terminal jobs per second since this run started, including successful and permanently failed jobs."/><MetricCard label="Active workers" value={metrics.active_workers ?? 0} detail={`${metrics.running ?? 0} jobs executing`} tone="purple" help="Worker processes with a recent Redis heartbeat. The secondary value counts jobs currently executing."/><MetricCard label="Errors" value={number.format(metrics.failed ?? 0)} detail={`${number.format(metrics.retrying ?? 0)} awaiting retry · ${number.format(metrics.retries ?? 0)} attempts`} tone="orange" help="Jobs that exhausted all attempts. Awaiting retry shows jobs in delayed retry queues; attempts is the cumulative number of retries scheduled."/></section>
    <section className="charts-grid"><Chart title="Queue and completion" subtitle="Work moving through the system" help="Orange shows jobs waiting to start; green shows cumulative successful completions. A growing orange line indicates workers cannot keep up with production." data={chartData} lines={[['queued','#f59e0b'],['completed','#39d98a']]}/><Chart title="Processing throughput" subtitle="Completed jobs per second" help="Cumulative average terminal throughput. Changes reveal acceleration, throttling, or reduced processing capacity during the run." data={chartData} lines={[['throughput','#5ba5ff']]}/><Chart title="Latency percentiles" subtitle="End-to-end processing latency (ms)" help="P50 is the median, P95 is slower than 95% of observations, and P99 highlights tail latency experienced by the slowest 1%." data={chartData} lines={[['p50_ms','#39d98a'],['p95_ms','#a78bfa'],['p99_ms','#fb7185']]}/><div className={`diagnosis ${bottleneck.severity}`}><div className="chart-title"><span><Gauge size={18}/> Automated diagnosis <HelpTip label="Automated diagnosis">Rule-based interpretation of queue growth, worker availability, and retry pressure. It identifies likely symptoms, not a definitive root cause.</HelpTip></span><small>Evidence-based estimate</small></div><div className="diagnosis-body"><Activity size={40}/><h3>{bottleneck.title}</h3><p>{bottleneck.detail}</p><dl><div><dt>Queue wait</dt><dd>{metrics.average_queue_ms ?? 0} ms</dd></div><div><dt>Processing</dt><dd>{metrics.average_processing_ms ?? 0} ms</dd></div><div><dt>P99</dt><dd>{metrics.p99_ms ?? 0} ms</dd></div></dl></div></div></section>
    <section className="panel technical"><div className="section-heading"><div><span className="eyebrow">Run configuration</span><h2>Experiment details</h2></div><span className={`connection ${live.connected ? 'online' : ''}`}><i/>{live.connected ? 'Live stream connected' : run.status === 'completed' ? 'Historical result' : 'Reconnecting'}</span></div><div className="detail-grid"><div><span>Producer concurrency <HelpTip label="Producer concurrency">Maximum simultaneous message publications configured for this run.</HelpTip></span><strong>{run.producer_concurrency}</strong></div><div><span>Target rate <HelpTip label="Target rate">Requested message publication rate; actual processing throughput can differ.</HelpTip></span><strong>{run.target_rate ? `${number.format(run.target_rate)}/s` : 'Unlimited'}</strong></div><div><span>Job duration <HelpTip label="Job duration">Configured workload time applied to each processing attempt.</HelpTip></span><strong>{run.duration_ms} ms</strong></div><div><span>Failure probability <HelpTip label="Failure probability">Configured independent failure chance for every attempt.</HelpTip></span><strong>{run.failure_probability * 100}%</strong></div><div><span>Maximum retries <HelpTip label="Maximum retries">Additional delayed attempts allowed before permanent failure.</HelpTip></span><strong>{run.max_retries}</strong></div><div><span>Dead-lettered <HelpTip label="Dead-lettered">Jobs moved to the dead-letter queue after exhausting every allowed retry.</HelpTip></span><strong>{metrics.dead_lettered ?? 0}</strong></div></div></section>
  </>
}

function Chart({ title, subtitle, help, data, lines }: { title: string; subtitle: string; help: string; data: Metrics[]; lines: Array<[keyof Metrics,string]> }) {
  return <div className="chart"><div className="chart-title"><span><BarChart3 size={18}/>{title}<HelpTip label={title}>{help}</HelpTip></span><small>{subtitle}</small></div><ResponsiveContainer width="100%" height={235}><LineChart data={data}><CartesianGrid stroke="#263044" strokeDasharray="3 3"/><XAxis dataKey="timestamp" hide/><YAxis stroke="#6f7b91" tickFormatter={value => compact.format(value)}/><Tooltip contentStyle={{background:'#111827',border:'1px solid #303b50',borderRadius:8}}/>{lines.map(([key,color]) => <Line key={String(key)} type="monotone" dataKey={key} stroke={color} dot={false} strokeWidth={2}/>)}</LineChart></ResponsiveContainer></div>
}

export default Shell
