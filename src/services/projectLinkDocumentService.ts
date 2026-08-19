import { apiClient } from '@/services/httpClient'
import type { ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'

/**
 * Fetch the link-only documents (Property / Government / Others) recorded
 * against a project. Unlike documentService, nothing here is an uploaded
 * file -- each record is just a name, category, and path/link back to
 * where the document actually lives.
 */
async function getLinkDocumentsForProject(projectId: string): Promise<ProjectLinkDocument[]> {
  try {
    return await apiClient.get<ProjectLinkDocument[]>(`/api/projects/${projectId}/link-documents`)
  } catch (error) {
    console.error(`Failed to fetch link documents for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch documents')
  }
}

async function createLinkDocument(
  projectId: string,
  category: ProjectLinkDocumentCategory,
  name: string,
  path: string,
): Promise<ProjectLinkDocument> {
  try {
    return await apiClient.post<ProjectLinkDocument>(`/api/projects/${projectId}/link-documents`, {
      category,
      name,
      path,
    })
  } catch (error) {
    console.error(`Failed to add link document for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add document')
  }
}

async function deleteLinkDocument(projectId: string, linkDocumentId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/projects/${projectId}/link-documents/${linkDocumentId}`)
  } catch (error) {
    console.error(`Failed to delete link document ${linkDocumentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete document')
  }
}

export const projectLinkDocumentService = {
  getLinkDocumentsForProject,
  createLinkDocument,
  deleteLinkDocument,
}
