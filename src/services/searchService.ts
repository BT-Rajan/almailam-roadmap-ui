import { apiClient } from '@/services/httpClient'
import type { SearchResult } from '@/types/Search'

/**
 * Search across all entities via backend API
 * Returns results from projects, clients, documents, users, tasks, and forms
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
 * Search for projects only via backend API
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
 * Search for clients only via backend API
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
 * Search for documents only via backend API
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
 * Search for users only via backend API
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
  searchClients,
  searchDocuments,
  searchUsers,
}
    }))

  const formResults: SearchResult[] = GOVERNMENT_FORMS.filter((form) =>
    matches(term, form.title, form.formCode, form.category),
  )
    .slice(0, RESULTS_PER_CATEGORY)
    .map((form) => ({
      id: form.id,
      category: 'Form',
      title: form.title,
      subtitle: `${form.formCode} · ${form.category}`,
      routeName: ROUTE_NAMES.GOVERNMENT_FORMS,
    }))

  const taskResults: SearchResult[] = TASKS.filter((task) => matches(term, task.title, task.assignedTo, task.status))
    .slice(0, RESULTS_PER_CATEGORY)
    .map((task) => ({
      id: task.id,
      category: 'Task',
      title: task.title,
      subtitle: `${task.assignedTo} · ${task.status}`,
      routeName: ROUTE_NAMES.TASKS,
    }))

  const userResults: SearchResult[] = USERS.filter((user) => matches(term, user.name, user.designation, user.role))
    .slice(0, RESULTS_PER_CATEGORY)
    .map((user) => ({
      id: user.id,
      category: 'User',
      title: user.name,
      subtitle: `${user.designation} · ${user.role}`,
      routeName: ROUTE_NAMES.ADMIN_USERS,
    }))

  return [...projectResults, ...documentResults, ...formResults, ...taskResults, ...userResults]
}

export const searchService = {
  search,
}
