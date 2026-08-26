import { useEffect, useState } from 'react'
import { api } from './api'
import type { Metrics } from './types'

export function useRunMetrics(runId: string | undefined, enabled = true) {
  const [metrics, setMetrics] = useState<Metrics>({})
  const [history, setHistory] = useState<Metrics[]>([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    setMetrics({})
    setHistory([])
    if (!runId || !enabled) {
      setConnected(false)
      return
    }
    const source = new EventSource(api.eventsUrl(runId))
    source.addEventListener('metrics', (event) => {
      const next = JSON.parse((event as MessageEvent).data) as Metrics
      setMetrics(next)
      setHistory((current) => [...current.slice(-179), next])
      setConnected(true)
      if (next.stream_finished === 1) {
        source.close()
        setConnected(false)
      }
    })
    source.onerror = () => setConnected(false)
    return () => source.close()
  }, [runId, enabled])

  return { metrics, history, connected }
}
