export type DocumentTemplateType = 'Quotation' | 'Contract'

export interface DocumentTemplate {
  id: string
  documentType: DocumentTemplateType
  originalFilename: string
  fileSizeBytes: number
  isDefault: boolean
  uploadedBy: string
  uploadedAt: string
}
