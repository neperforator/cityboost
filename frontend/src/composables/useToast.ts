import { ref } from 'vue'
import type { Toast } from '@/types'

const toasts = ref<Toast[]>([])
let id = 0

export function useToast() {
  const add = (message: string, type: Toast['type'] = 'info', duration = 4000): Toast => {
    const toast: Toast = { id: ++id, message, type, duration }
    toasts.value.push(toast)
    if (duration > 0) {
      setTimeout(() => remove(toast.id), duration)
    }
    return toast
  }

  const remove = (toastId: number): void => {
    const idx = toasts.value.findIndex(t => t.id === toastId)
    if (idx !== -1) toasts.value.splice(idx, 1)
  }

  return {
    toasts,
    success: (msg: string, duration = 4000) => add(msg, 'success', duration),
    error: (msg: string, duration = 5000) => add(msg, 'error', duration),
    info: (msg: string, duration = 4000) => add(msg, 'info', duration),
    warning: (msg: string, duration = 5000) => add(msg, 'warning', duration),
    remove,
  }
}
