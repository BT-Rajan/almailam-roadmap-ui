export type SearchResultCategory = 'Project' | 'Document' | 'Form' | 'Task' | 'User'

export interface SearchResult {
  id: string
  category: SearchResultCategory
  title: string
  subtitle: string
  routeName: string
  params?: Record<string, string>
}

export interface SearchResultGroup {
  category: SearchResultCategory
  results: SearchResult[]
}
