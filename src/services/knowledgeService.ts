import { apiClient, asError } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { KnowledgeAskResult, KnowledgeDocument, KnowledgeStatus } from '@/types/Knowledge'

/**
 * Whether the knowledgebase assistant is enabled -- available to any user
 * with Knowledgebase view access, not just admins (contrast with the full
 * /api/ai/configuration, which stays Administration-only).
 */
async function getStatus(): Promise<KnowledgeStatus> {
  try {
    return await apiClient.get<KnowledgeStatus>('/api/knowledge/status')
  } catch (error) {
    console.error('Failed to fetch knowledgebase status:', error)
    throw asError(error, 'Failed to fetch status')
  }
}

/**
 * List all knowledgebase documents from backend API
 */
async function getDocuments(): Promise<KnowledgeDocument[]> {
  try {
    return await apiClient.get<KnowledgeDocument[]>('/api/knowledge/documents')
  } catch (error) {
    console.error('Failed to fetch knowledgebase documents:', error)
    throw asError(error, 'Failed to fetch documents')
  }
}

/**
 * Upload a knowledgebase document via backend API.
 * Note: multipart/form-data, so this bypasses apiClient (which always
 * JSON-encodes) the same way documentService.uploadDocument does.
 */
async function uploadDocument(file: File, title: string): Promise<KnowledgeDocument> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)
  if (title.trim()) formData.append('title', title.trim())

  const doRequest = () =>
    fetch('/api/knowledge/documents', {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) {
        response = await doRequest()
      }
    }

    if (!response.ok) {
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }

    return (await response.json()) as KnowledgeDocument
  } catch (error) {
    console.error('Failed to upload knowledgebase document:', error)
    throw asError(error, 'Failed to upload document')
  }
}

/**
 * Activate/deactivate a knowledgebase document via backend API
 */
async function setActive(documentId: string, isActive: boolean): Promise<KnowledgeDocument> {
  try {
    return await apiClient.patch<KnowledgeDocument>(`/api/knowledge/documents/${documentId}`, { isActive })
  } catch (error) {
    console.error(`Failed to update knowledgebase document ${documentId}:`, error)
    throw asError(error, 'Failed to update document')
  }
}

/**
 * Delete a knowledgebase document via backend API
 */
async function deleteDocument(documentId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/knowledge/documents/${documentId}`)
  } catch (error) {
    console.error(`Failed to delete knowledgebase document ${documentId}:`, error)
    throw asError(error, 'Failed to delete document')
  }
}

/**
 * Ask a question, grounded strictly in one document (documentId) or all
 * active documents (documentId omitted), via backend API
 */
async function ask(question: string, documentId?: string): Promise<KnowledgeAskResult> {
  try {
    // A real LLM call can legitimately take well past the default 20s
    // request timeout -- AI Configuration alone allows up to 300s per
    // attempt, times (retryLimit + 1) attempts, times up to 2 providers
    // in providerPriority (see backend ai_service.generate_text). Even
    // at the *defaults* (30s, 2 retries, 2 providers) that's up to 180s.
    // 180s here is a reasonable practical ceiling for a normal question,
    // not an attempt to cover every extreme an admin could configure.
    return await apiClient.post<KnowledgeAskResult>(
      '/api/knowledge/ask',
      { question, documentId: documentId || undefined },
      { timeoutMs: 180_000 },
    )
  } catch (error) {
    console.error('Failed to ask knowledgebase question:', error)
    throw asError(error, 'Failed to get an answer')
  }
}

export const knowledgeService = {
  getStatus,
  getDocuments,
  uploadDocument,
  setActive,
  deleteDocument,
  ask,
}
