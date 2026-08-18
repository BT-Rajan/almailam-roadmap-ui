export type ResultDialogStatus = 'success' | 'error'

export interface ResultDialogState {
  isOpen: boolean
  status: ResultDialogStatus
  title: string
  description?: string
}
