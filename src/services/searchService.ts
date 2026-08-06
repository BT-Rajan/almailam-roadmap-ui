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

export const searchService = {
  search,
  searchProjects,
  searchDocuments,
  searchUsers,
}
