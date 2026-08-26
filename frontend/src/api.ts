import type { Run, RunCreate } from './types'

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  listRuns: () => request<Run[]>('/runs'),
  getRun: (id: string) => request<Run>(`/runs/${id}`),
  createRun: (payload: RunCreate) => request<Run>('/runs', { method: 'POST', body: JSON.stringify(payload) }),
  cancelRun: (id: string) => request(`/runs/${id}/cancel`, { method: 'POST' }),
  deleteRun: (id: string) => request<void>(`/runs/${id}`, { method: 'DELETE' }),
  eventsUrl: (id: string) => `${BASE}/runs/${id}/events`,
}
