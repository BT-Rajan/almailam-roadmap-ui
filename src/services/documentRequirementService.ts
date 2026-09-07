import { apiClient } from '@/services/httpClient'
import type { DocumentRequirement, DocumentRequirementLink, DocumentRequirementTargetType } from '@/types/DocumentRequirement'

async function getRequirements(): Promise<DocumentRequirement[]> {
  try {
    return await apiClient.get<DocumentRequirement[]>('/api/document-requirements')
  } catch (error) {
    console.error('Failed to fetch document requirements:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document requirements')
  }
}

async function createRequirement(name: string, description?: string): Promise<DocumentRequirement> {
  try {
    return await apiClient.post<DocumentRequirement>('/api/document-requirements', { name, description })
  } catch (error) {
    console.error('Failed to add document requirement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add document requirement')
  }
}

async function updateRequirement(
  requirementId: string, fields: { name?: string; description?: string },
): Promise<DocumentRequirement> {
  try {
    return await apiClient.patch<DocumentRequirement>(`/api/document-requirements/${requirementId}`, fields)
  } catch (error) {
    console.error(`Failed to update document requirement ${requirementId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update document requirement')
  }
}

async function removeRequirement(requirementId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/document-requirements/${requirementId}`)
  } catch (error) {
    console.error(`Failed to remove document requirement ${requirementId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove document requirement')
  }
}

/** The reference checklist for a specific Design/Permit/Supervision target -- used on a project's own tabs. */
async function getLinksForTarget(
  targetType: DocumentRequirementTargetType, targetCatalogId: string,
): Promise<DocumentRequirementLink[]> {
  try {
    const query = new URLSearchParams({ targetType, targetCatalogId }).toString()
    return await apiClient.get<DocumentRequirementLink[]>(`/api/document-requirements/links?${query}`)
  } catch (error) {
    console.error(`Failed to fetch document requirement links for ${targetType} ${targetCatalogId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document requirements')
  }
}

/** Every target a requirement is linked to -- used by the admin reuse panel. */
async function getLinksForRequirement(requirementId: string): Promise<DocumentRequirementLink[]> {
  try {
    return await apiClient.get<DocumentRequirementLink[]>(`/api/document-requirements/${requirementId}/links`)
  } catch (error) {
    console.error(`Failed to fetch links for document requirement ${requirementId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document requirement links')
  }
}

async function addLink(
  requirementId: string, targetType: DocumentRequirementTargetType, targetCatalogId: string,
): Promise<DocumentRequirementLink> {
  try {
    return await apiClient.post<DocumentRequirementLink>('/api/document-requirements/links', {
      requirementId, targetType, targetCatalogId,
    })
  } catch (error) {
    console.error('Failed to link document requirement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to link document requirement')
  }
}

async function removeLink(linkId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/document-requirements/links/${linkId}`)
  } catch (error) {
    console.error(`Failed to remove document requirement link ${linkId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove document requirement link')
  }
}

export const documentRequirementService = {
  getRequirements,
  createRequirement,
  updateRequirement,
  removeRequirement,
  getLinksForTarget,
  getLinksForRequirement,
  addLink,
  removeLink,
}
