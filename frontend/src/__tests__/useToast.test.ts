import { describe, it, expect, beforeEach } from 'vitest'
import { useToast } from '@/composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    // Reset the shared toasts array
    const toast = useToast()
    while (toast.toasts.value.length) {
      toast.remove(toast.toasts.value[0].id)
    }
  })

  it('adds a toast', () => {
    const toast = useToast()
    toast.success('Test message')
    expect(toast.toasts.value).toHaveLength(1)
    expect(toast.toasts.value[0].message).toBe('Test message')
    expect(toast.toasts.value[0].type).toBe('success')
  })

  it('removes a toast by id', () => {
    const toast = useToast()
    const t = toast.info('Remove me')
    expect(toast.toasts.value).toHaveLength(1)
    toast.remove(t.id)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('auto-removes after duration', async () => {
    const toast = useToast()
    toast.error('Ephemeral', 1) // 1ms duration
    expect(toast.toasts.value).toHaveLength(1)
    await new Promise(r => setTimeout(r, 10))
    expect(toast.toasts.value).toHaveLength(0)
  })
})
