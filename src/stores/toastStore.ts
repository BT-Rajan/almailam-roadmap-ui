import { defineStore } from 'pinia'

import type { ToastMessage, ToastVariant } from '@/types/Toast'

const DEFAULT_TOAST_DURATION = 4000

export const useToastStore = defineStore('toast', {
  state: () => ({
    toasts: [] as ToastMessage[],
  }),

  actions: {
    show(variant: ToastVariant, title: string, description?: string, duration = DEFAULT_TOAST_DURATION) {
      const id = crypto.randomUUID()
      this.toasts.push({ id, variant, title, description, duration })

      if (duration > 0) {
        setTimeout(() => this.dismiss(id), duration)
      }

      return id
    },

    dismiss(id: string) {
      this.toasts = this.toasts.filter((toast) => toast.id !== id)
    },
  },
})
