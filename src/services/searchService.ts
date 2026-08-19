import { apiClient } from '@/services/httpClient'
import type { SearchResult } from '@/types/Search'

/**
 * Search across all entities via the backend API.
 * Returns results from projects, documents, forms, tasks, and users.
 */
async function search(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to perform search')
  }
}

/**
 * Search for clients only via the backend API.
 */
async function searchClients(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/clients?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search clients:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search clients')
  }
}

/**
 * Search for projects only via the backend API.
 */
async function searchProjects(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/projects?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search projects:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search projects')
  }
}

/**
 * Search for documents only via the backend API.
 */
async function searchDocuments(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/documents?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search documents:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search documents')
  }
}

/**
 * Search for users only via the backend API.
 */
async function searchUsers(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/users?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search users:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search users')
  }
}

/**
 * Search for contracts only via the backend API.
 */
async function searchContracts(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/contracts?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search contracts:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search contracts')
  }
}

/**
 * Search for quotations only via the backend API.
 */
async function searchQuotations(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/quotations?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search quotations:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search quotations')
  }
}

/**
 * Search for government submissions only via the backend API.
 */
async function searchSubmissions(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/submissions?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search submissions:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search submissions')
  }
}

/**
 * Search for payments only via the backend API.
 */
async function searchPayments(query: string): Promise<SearchResult[]> {
  try {
    if (!query.trim()) {
      return []
    }

    return await apiClient.get<SearchResult[]>(`/api/search/payments?q=${encodeURIComponent(query)}`)
  } catch (error) {
    console.error('Failed to search payments:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to search payments')
  }
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
