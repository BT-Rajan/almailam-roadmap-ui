import { useToastStore } from '@/stores/toastStore'

export function useToast() {
  const toastStore = useToastStore()

  return {
    success: (title: string, description?: string) => toastStore.show('success', title, description),
    error: (title: string, description?: string) => toastStore.show('error', title, description),
    warning: (title: string, description?: string) => toastStore.show('warning', title, description),
    info: (title: string, description?: string) => toastStore.show('info', title, description),
  }
}
