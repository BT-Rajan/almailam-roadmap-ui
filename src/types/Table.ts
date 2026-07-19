export type SortDirection = 'asc' | 'desc'

export type ColumnAlign = 'left' | 'center' | 'right'

export interface SmartTableColumn<T> {
  key: keyof T & string
  label: string
  sortable?: boolean
  align?: ColumnAlign
  width?: string
}
