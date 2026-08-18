import { defineStore } from 'pinia'

import type { ResultDialogState } from '@/types/ResultDialog'

// Deliberately separate from toastStore: a toast is a passive, auto-
// dismissing notification, useful for routine feedback that doesn't need
// acknowledgment. This is for actions where the person should explicitly
// confirm they've seen the outcome (success or failure) before moving on
// -- e.g. every create/edit/delete-style action in the Clients module.
export const useResultDialogStore = defineStore('resultDialog', {
  state: (): ResultDialogState => ({
    isOpen: false,
    status: 'success',
    title: '',
    description: undefined,
  }),

  actions: {
    showSuccess(title: string, description?: string) {
      this.status = 'success'
      this.title = title
      this.description = description
      this.isOpen = true
    },

    showError(title: string, description?: string) {
      this.status = 'error'
      this.title = title
      this.description = description
      this.isOpen = true
    },

    close() {
      this.isOpen = false
    },
  },
})
