import type { AIProviderId } from '@/types/AiConfig'
import type { AIConfidence } from '@/types/AiReview'

export interface AIInteraction {
  id: string
  prompt: string
  templateName?: string
  provider: AIProviderId
  summary: string
  details: string
  confidence: AIConfidence
  suggestedActions: string[]
  timestamp: string
}
