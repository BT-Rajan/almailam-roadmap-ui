export type SearchResultCategory =
  | 'Client'
  | 'Project'
  | 'Document'
  | 'Form'
  | 'Task'
  | 'User'
  | 'Contract'
  | 'Quotation'
  | 'Submission'
  | 'Payment'

export interface SearchResult {
  id: string
  category: SearchResultCategory
  title: string
  subtitle: string
  routeName: string
  params?: Record<string, string>
  // Query-string params for results that deep-link into a tab of another
  // page (e.g. a contract lives on the project workspace's Contract tab)
  // rather than having a standalone route of their own.
  query?: Record<string, string>
}

export interface SearchResultGroup {
  category: SearchResultCategory
  results: SearchResult[]
}
