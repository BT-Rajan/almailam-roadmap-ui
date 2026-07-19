export type AIConfidence = 'high' | 'medium' | 'low'

export interface ExtractedField {
  label: string
  value: string
  confidence: AIConfidence
}

export interface DocumentAIReview {
  documentId: string
  summary: string
  details: string
  confidence: AIConfidence
  extractedFields: ExtractedField[]
  suggestions: string[]
}
