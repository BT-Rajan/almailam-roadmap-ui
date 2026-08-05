import { apiClient } from '@/services/httpClient'
import type { DocumentVersion, ProjectDocument } from '@/types/Document'

/**
 * Fetch all documents from backend API
 */
async function getDocuments(): Promise<ProjectDocument[]> {
  try {
    return await apiClient.get<ProjectDocument[]>('/api/documents')
  } catch (error) {
    console.error('Failed to fetch documents:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch documents')
  }
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
  try {
    return await apiClient.get<ProjectDocument[]>(`/api/projects/${projectId}/documents`)
  } catch (error) {
    console.error(`Failed to fetch documents for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch documents')
  }
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
  getDocumentById,
  getDocumentsByProject,
  getDocumentVersions,
  uploadDocument,
  deleteDocument,
  downloadDocument,
}
