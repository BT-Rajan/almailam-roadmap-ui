import { DOCUMENTS } from '@/mock/documents'
import { DOCUMENT_VERSIONS } from '@/mock/documentVersions'
import type { DocumentVersion, ProjectDocument } from '@/types/Document'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getDocuments(): Promise<ProjectDocument[]> {
  await simulateNetworkDelay()
  return [...DOCUMENTS]
}

async function getDocumentById(documentId: string): Promise<ProjectDocument | undefined> {
  await simulateNetworkDelay()
  return DOCUMENTS.find((document) => document.id === documentId)
}

async function getDocumentsByProject(projectId: string): Promise<ProjectDocument[]> {
  await simulateNetworkDelay()
  return DOCUMENTS.filter((document) => document.projectId === projectId)
}

async function getDocumentVersions(documentId: string): Promise<DocumentVersion[]> {
  await simulateNetworkDelay()
  return DOCUMENT_VERSIONS.filter((version) => version.documentId === documentId)
}

export const documentService = {
  getDocuments,
  getDocumentById,
  getDocumentsByProject,
  getDocumentVersions,
}
