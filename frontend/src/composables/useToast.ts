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
    success: (msg: string) => add(msg, 'success'),
    error: (msg: string) => add(msg, 'error', 5000),
    info: (msg: string) => add(msg, 'info'),
    warning: (msg: string) => add(msg, 'warning', 5000),
    remove,
  }
}
