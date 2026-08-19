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
  originalFilename: string
}

export type DocumentViewMode = 'grid' | 'table'

// The three project-level categories a document can be added under with
// just a name and a path/link -- the file itself is stored outside the
// app (a shared drive, a government portal, a scan on the office server).
// "Customer ID" is shown alongside these in the Documents tab but is a
// fourth, read-only category sourced from the client's own onboarding
// documents (ClientDocument), not this type.
export type ProjectLinkDocumentCategory = 'Property' | 'Government' | 'Others'

export interface ProjectLinkDocument {
  id: string
  projectId: string
  category: ProjectLinkDocumentCategory
  name: string
  path: string
  addedBy: string
  addedDate: string
}

export interface DocumentVersion {
  id: string
  documentId: string
  revision: string
  uploadedBy: string
  uploadDate: string
  notes: string
  originalFilename: string
}
