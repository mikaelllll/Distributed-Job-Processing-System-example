import { describe, expect, it } from 'vitest'
import { detectBottleneck, mergeMetricHistory } from './components'

describe('detectBottleneck', () => {
  it('reports missing worker capacity when jobs are queued', () => {
    expect(detectBottleneck({ queued: 100, active_workers: 0 }).title).toBe('No worker capacity')
  })

  it('reports a balanced system when no pressure signal exists', () => {
    expect(detectBottleneck({ queued: 1, completed: 100, active_workers: 4 }).severity).toBe('healthy')
  })
})

describe('mergeMetricHistory', () => {
  it('orders overlapping persisted and live samples without duplicating timestamps', () => {
    const result = mergeMetricHistory(
      [
        { timestamp: '2026-08-26T03:00:02Z', completed: 20 },
        { timestamp: '2026-08-26T03:00:04Z', completed: 40 },
      ],
      [
        { timestamp: '2026-08-26T03:00:03Z', completed: 30 },
        { timestamp: '2026-08-26T03:00:04Z', completed: 41 },
      ],
    )

    expect(result.map((sample) => sample.completed)).toEqual([20, 30, 41])
  })
})
