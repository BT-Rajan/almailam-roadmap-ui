import { apiClient, asError } from '@/services/httpClient'
import type { ChecklistItem, DocumentRequirement, DocumentRequirementLink, DocumentRequirementTargetType } from '@/types/DocumentRequirement'

async function getRequirements(): Promise<DocumentRequirement[]> {
  try {
    return await apiClient.get<DocumentRequirement[]>('/api/document-requirements')
  } catch (error) {
    console.error('Failed to fetch document requirements:', error)
    throw asError(error, 'Failed to fetch document requirements')
  }
}

async function createRequirement(name: string, description?: string): Promise<DocumentRequirement> {
  try {
    return await apiClient.post<DocumentRequirement>('/api/document-requirements', { name, description })
  } catch (error) {
    console.error('Failed to add document requirement:', error)
    throw asError(error, 'Failed to add document requirement')
  }
}

async function updateRequirement(
  requirementId: string, fields: { name?: string; description?: string },
): Promise<DocumentRequirement> {
  try {
    return await apiClient.patch<DocumentRequirement>(`/api/document-requirements/${requirementId}`, fields)
  } catch (error) {
    console.error(`Failed to update document requirement ${requirementId}:`, error)
    throw asError(error, 'Failed to update document requirement')
  }
}

async function removeRequirement(requirementId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/document-requirements/${requirementId}`)
  } catch (error) {
    console.error(`Failed to remove document requirement ${requirementId}:`, error)
    throw asError(error, 'Failed to remove document requirement')
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
    throw asError(error, 'Failed to fetch document requirements')
  }
}

/** Every target a requirement is linked to -- used by the admin reuse panel. */
async function getLinksForRequirement(requirementId: string): Promise<DocumentRequirementLink[]> {
  try {
    return await apiClient.get<DocumentRequirementLink[]>(`/api/document-requirements/${requirementId}/links`)
  } catch (error) {
    console.error(`Failed to fetch links for document requirement ${requirementId}:`, error)
    throw asError(error, 'Failed to fetch document requirement links')
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
    throw asError(error, 'Failed to link document requirement')
  }
}

async function removeLink(linkId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/document-requirements/links/${linkId}`)
  } catch (error) {
    console.error(`Failed to remove document requirement link ${linkId}:`, error)
    throw asError(error, 'Failed to remove document requirement link')
  }
}

// Handover document checklist (#4/#5) -- a project's own copy of the
// reference list above, plus its own fulfillment state. One GET/PUT
// pair per track (see api/projects.py's own _checklist_out/
// _set_checklist_item, shared the same way there).
async function getDesignChecklist(projectNo: string, activityId: string): Promise<ChecklistItem[]> {
  try {
    return await apiClient.get<ChecklistItem[]>(`/api/projects/${projectNo}/design-activities/${activityId}/checklist`)
  } catch (error) {
    console.error(`Failed to fetch design checklist for activity ${activityId}:`, error)
    throw asError(error, 'Failed to fetch design checklist')
  }
}

async function setDesignChecklistItem(
  projectNo: string, activityId: string, linkId: string, fulfilled: boolean, documentId?: string,
): Promise<ChecklistItem[]> {
  try {
    return await apiClient.put<ChecklistItem[]>(
      `/api/projects/${projectNo}/design-activities/${activityId}/checklist/${linkId}`, { fulfilled, documentId },
    )
  } catch (error) {
    console.error(`Failed to update design checklist item ${linkId}:`, error)
    throw asError(error, 'Failed to update design checklist item')
  }
}

async function getPermitChecklist(projectNo: string, permitId: string): Promise<ChecklistItem[]> {
  try {
    return await apiClient.get<ChecklistItem[]>(`/api/projects/${projectNo}/permits/${permitId}/checklist`)
  } catch (error) {
    console.error(`Failed to fetch permit checklist for permit ${permitId}:`, error)
    throw asError(error, 'Failed to fetch permit checklist')
  }
}

async function setPermitChecklistItem(
  projectNo: string, permitId: string, linkId: string, fulfilled: boolean, documentId?: string,
): Promise<ChecklistItem[]> {
  try {
    return await apiClient.put<ChecklistItem[]>(
      `/api/projects/${projectNo}/permits/${permitId}/checklist/${linkId}`, { fulfilled, documentId },
    )
  } catch (error) {
    console.error(`Failed to update permit checklist item ${linkId}:`, error)
    throw asError(error, 'Failed to update permit checklist item')
  }
}

async function getSupervisionChecklist(projectNo: string, activityId: string): Promise<ChecklistItem[]> {
  try {
    return await apiClient.get<ChecklistItem[]>(`/api/projects/${projectNo}/supervision-activities/${activityId}/checklist`)
  } catch (error) {
    console.error(`Failed to fetch supervision checklist for activity ${activityId}:`, error)
    throw asError(error, 'Failed to fetch supervision checklist')
  }
}

async function setSupervisionChecklistItem(
  projectNo: string, activityId: string, linkId: string, fulfilled: boolean, documentId?: string,
): Promise<ChecklistItem[]> {
  try {
    return await apiClient.put<ChecklistItem[]>(
      `/api/projects/${projectNo}/supervision-activities/${activityId}/checklist/${linkId}`, { fulfilled, documentId },
    )
  } catch (error) {
    console.error(`Failed to update supervision checklist item ${linkId}:`, error)
    throw asError(error, 'Failed to update supervision checklist item')
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
  getDesignChecklist,
  setDesignChecklistItem,
  getPermitChecklist,
  setPermitChecklistItem,
  getSupervisionChecklist,
  setSupervisionChecklistItem,
}
