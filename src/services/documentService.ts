import { DOCUMENTS } from '@/mock/documents'
import type { ProjectDocument } from '@/types/Document'
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

export const documentService = {
  getDocuments,
  getDocumentById,
  getDocumentsByProject,
}
