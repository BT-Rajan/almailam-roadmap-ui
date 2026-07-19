import { AI_DOCUMENT_REVIEWS } from '@/mock/aiReviews'
import type { DocumentAIReview } from '@/types/AiReview'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const AI_THINKING_DELAY_MS = 900

async function getDocumentReview(documentId: string): Promise<DocumentAIReview | undefined> {
  await simulateNetworkDelay(AI_THINKING_DELAY_MS)
  return AI_DOCUMENT_REVIEWS.find((review) => review.documentId === documentId)
}

export const aiService = {
  getDocumentReview,
}
