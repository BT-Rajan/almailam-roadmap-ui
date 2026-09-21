import { apiClient, asError, RequestCancelledError } from '@/services/httpClient'
import type { SearchResult } from '@/types/Search'

/** Shared implementation behind every searchX() below -- each just supplies its own
 * endpoint path and the entity label used in log/error messages. An empty label keeps
 * search()'s original wording ("Failed to search:" / "Failed to perform search"). `signal`
 * lets a caller cancel an in-flight search (e.g. search-as-you-type superseded by a newer
 * keystroke) -- a cancellation propagates as-is (RequestCancelledError), not wrapped into
 * the same "search failed" error a real failure gets, so callers can tell them apart. */
async function runSearch(path: string, query: string, entityLabel = '', signal?: AbortSignal): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`${path}?q=${encodeURIComponent(query)}`, { signal })
  } catch (error) {
    if (error instanceof RequestCancelledError) throw error
    const suffix = entityLabel ? ` ${entityLabel}` : ''
    console.error(`Failed to search${suffix}:`, error)
    throw asError(error, entityLabel ? `Failed to search ${entityLabel}` : 'Failed to perform search')
  }
}

/**
 * Search across all entities via the backend API.
 * Returns results from projects, documents, forms, tasks, and users.
 */
async function search(query: string, signal?: AbortSignal): Promise<SearchResult[]> {
  return runSearch('/api/search', query, '', signal)
}

/**
 * Search for clients only via the backend API.
 */
async function searchClients(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/clients', query, 'clients')
}

/**
 * Search for projects only via the backend API.
 */
async function searchProjects(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/projects', query, 'projects')
}

/**
 * Search for documents only via the backend API.
 */
async function searchDocuments(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/documents', query, 'documents')
}

/**
 * Search for users only via the backend API.
 */
async function searchUsers(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/users', query, 'users')
}

/**
 * Search for contracts only via the backend API.
 */
async function searchContracts(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/contracts', query, 'contracts')
}

/**
 * Search for quotations only via the backend API.
 */
async function searchQuotations(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/quotations', query, 'quotations')
}

/**
 * Search for government submissions only via the backend API.
 */
async function searchSubmissions(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/submissions', query, 'submissions')
}

/**
 * Search for payments only via the backend API.
 */
async function searchPayments(query: string): Promise<SearchResult[]> {
  return runSearch('/api/search/payments', query, 'payments')
}

export const searchService = {
  search,
  searchClients,
  searchProjects,
  searchDocuments,
  searchUsers,
  searchContracts,
  searchQuotations,
  searchSubmissions,
  searchPayments,
}
