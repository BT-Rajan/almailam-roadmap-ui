import { apiClient } from '@/services/httpClient'
import type { DocumentVersion, ProjectDocument } from '@/types/Document'
import type { PagedResponse, PageParams } from '@/types/Pagination'
import { fetchAllPages } from '@/utils/fetchAllPages'

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * Fetch a single page of documents from the backend API. Prefer this over
 * getDocuments() for any UI that displays/paginates the list directly,
 * since it only asks the server for one page at a time instead of the
 * whole table.
 */
async function getDocumentsPage(
  params: PageParams & { projectId?: string; status?: string; type?: string } = {},
): Promise<PagedResponse<ProjectDocument>> {
  try {
    const query = buildQuery({
      projectId: params.projectId,
      status: params.status,
      type: params.type,
      search: params.search,
      sort: params.sort,
      page: params.page,
      pageSize: params.pageSize,
    })
    return await apiClient.get<PagedResponse<ProjectDocument>>(`/api/documents${query}`)
  } catch (error) {
    console.error('Failed to fetch documents:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch documents')
  }
}

/**
 * Fetch every document from the backend API as a flat array. Internally
 * walks the paginated endpoint page by page (each request is still bounded
 * server-side) so existing callers that need the full list don't have to
 * change.
 */
async function getDocuments(): Promise<ProjectDocument[]> {
  return fetchAllPages<ProjectDocument>((page, pageSize) => getDocumentsPage({ page, pageSize }))
}

/**
 * Fetch a specific document by ID from backend API
 */
async function getDocumentById(documentId: string): Promise<ProjectDocument | undefined> {
  try {
    return await apiClient.get<ProjectDocument>(`/api/documents/${documentId}`)
  } catch (error) {
    console.error(`Failed to fetch document ${documentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document')
  }
}

/**
 * Fetch documents for a specific project from backend API
 */
async function getDocumentsByProject(projectId: string): Promise<ProjectDocument[]> {
  return fetchAllPages<ProjectDocument>((page, pageSize) => getDocumentsPage({ projectId, page, pageSize }))
}

/**
 * Fetch version history for a document from backend API
 */
async function getDocumentVersions(documentId: string): Promise<DocumentVersion[]> {
  try {
    return await apiClient.get<DocumentVersion[]>(`/api/documents/${documentId}/versions`)
  } catch (error) {
    console.error(`Failed to fetch versions for document ${documentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document versions')
  }
}

/**
 * Upload a new document via backend API
 * Note: This uses multipart/form-data, handled specially by the API client
 */
async function uploadDocument(file: File, projectId: string, metadata?: Record<string, string>): Promise<ProjectDocument> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    // Use fetch directly for file upload since apiClient assumes JSON
    const response = await fetch('/api/documents/upload', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('almailam-access-token') || ''}`,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`)
    }

    return (await response.json()) as ProjectDocument
  } catch (error) {
    console.error('Failed to upload document:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload document')
  }
}

/**
 * Delete a document via backend API
 */
async function deleteDocument(documentId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/documents/${documentId}`)
  } catch (error) {
    console.error(`Failed to delete document ${documentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete document')
  }
}

/**
 * Download a document from backend API
 */
async function downloadDocument(documentId: string): Promise<Blob> {
  try {
    const response = await fetch(`/api/documents/${documentId}/download`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('almailam-access-token') || ''}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }

    return await response.blob()
  } catch (error) {
    console.error(`Failed to download document ${documentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to download document')
  }
}

export const documentService = {
  getDocuments,
  getDocumentsPage,
  getDocumentById,
  getDocumentsByProject,
  getDocumentVersions,
  uploadDocument,
  deleteDocument,
  downloadDocument,
}
