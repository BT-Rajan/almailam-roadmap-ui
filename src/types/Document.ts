export type DocumentType = 'Drawing' | 'Report' | 'Contract' | 'Quotation' | 'Municipality Form' | 'Calculation Sheet'

export type DocumentStatus = 'Draft' | 'Under Review' | 'Approved' | 'Rejected'

export interface ProjectDocument {
  id: string
  projectId: string
  title: string
  type: DocumentType
  revision: string
  uploadedBy: string
  uploadDate: string
  status: DocumentStatus
  fileSize: string
}

export type DocumentViewMode = 'grid' | 'table'

export interface DocumentVersion {
  id: string
  documentId: string
  revision: string
  uploadedBy: string
  uploadDate: string
  notes: string
}
