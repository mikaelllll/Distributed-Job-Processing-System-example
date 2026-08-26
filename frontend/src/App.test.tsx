import { describe, expect, it } from 'vitest'
import { modeForJobCount } from './App'

describe('modeForJobCount', () => {
  it.each(['audit', 'benchmark'] as const)(
    'preserves %s for real executions at the one-million boundary',
    (mode) => {
      expect(modeForJobCount(1_000_000, mode)).toBe(mode)
    },
  )

  it('selects simulation above the real-message safety limit', () => {
    expect(modeForJobCount(1_000_001, 'benchmark')).toBe('simulation')
  })

  it('returns to benchmark when reducing a simulated run', () => {
    expect(modeForJobCount(100_000, 'simulation')).toBe('benchmark')
  })
})
