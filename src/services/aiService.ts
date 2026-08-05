import { apiClient } from '@/services/httpClient'
import type { DocumentAIReview } from '@/types/AiReview'

/**
 * Get AI review for a document from backend API
 */
async function getDocumentReview(documentId: string): Promise<DocumentAIReview | undefined> {
  try {
    return await apiClient.get<DocumentAIReview>(`/api/ai/documents/${documentId}/review`)
  } catch (error) {
    console.error(`Failed to fetch document review:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch review')
  }
}

export const aiService = {
  getDocumentReview,
}
