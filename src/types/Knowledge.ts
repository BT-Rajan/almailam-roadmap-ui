export interface KnowledgeDocument {
  id: string
  title: string
  originalFilename: string
  fileSize: string
  contentType: 'pdf' | 'docx' | 'txt'
  charCount: number
  truncated: boolean
  extractionOk: boolean
  extractionError: string
  isActive: boolean
  uploadedBy: string
  createdAt: string
}

export interface KnowledgeAskResult {
  answer: string
  sourceDocumentIds: string[]
  cached: boolean
}

export interface KnowledgeQAEntry extends KnowledgeAskResult {
  id: string
  question: string
  askedAt: string
}
