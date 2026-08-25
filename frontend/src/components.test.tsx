import { describe, expect, it } from 'vitest'
import { detectBottleneck } from './components'

describe('detectBottleneck', () => {
  it('reports missing worker capacity when jobs are queued', () => {
    expect(detectBottleneck({ queued: 100, active_workers: 0 }).title).toBe('No worker capacity')
  })

  it('reports a balanced system when no pressure signal exists', () => {
    expect(detectBottleneck({ queued: 1, completed: 100, active_workers: 4 }).severity).toBe('healthy')
  })
})

