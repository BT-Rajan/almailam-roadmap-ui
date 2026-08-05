import { apiClient } from '@/services/httpClient'
import type { AIProviderId } from '@/types/AiConfig'
import type { AIInteraction } from '@/types/AiAssistant'

/**
 * Get AI Assistant response from backend API
 * Uses configured AI provider (Gemini, Claude, etc.)
 */
async function getResponse(
  prompt: string,
  provider: AIProviderId,
  templateName?: string
): Promise<AIInteraction> {
  try {
    return await apiClient.post<AIInteraction>('/api/ai/assistant/response', {
      prompt,
      provider,
      template_name: templateName,
    })
  } catch (error) {
    console.error('Failed to get AI response:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to get AI response')
  }
}

/**
 * Get AI response for contract analysis
 */
async function analyzeContract(contractId: string): Promise<AIInteraction> {
  try {
    return await apiClient.post<AIInteraction>('/api/ai/assistant/analyze-contract', {
      contract_id: contractId,
    })
  } catch (error) {
    console.error('Failed to analyze contract:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to analyze contract')
  }
}

/**
 * Get AI response for document review
 */
async function reviewDocument(documentId: string): Promise<AIInteraction> {
  try {
    return await apiClient.post<AIInteraction>('/api/ai/assistant/review-document', {
      document_id: documentId,
    })
  } catch (error) {
    console.error('Failed to review document:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to review document')
  }
}

/**
 * Get AI response for risk assessment
 */
async function assessRisk(entityType: string, entityId: string): Promise<AIInteraction> {
  try {
    return await apiClient.post<AIInteraction>('/api/ai/assistant/assess-risk', {
      entity_type: entityType,
      entity_id: entityId,
    })
  } catch (error) {
    console.error('Failed to assess risk:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to assess risk')
  }
}

export const aiAssistantService = {
  getResponse,
  analyzeContract,
  reviewDocument,
  assessRisk,
}
