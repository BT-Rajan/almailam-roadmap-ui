import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/httpClient'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { ProjectDocument } from '@/types/Document'

// sampleFileName is read-only, set only via uploadSampleFile below --
// never part of the create/update form payload.
export type FormInput = Omit<GovernmentForm, 'id' | 'sampleFileName'>
export type AuthorityInput = Omit<GovernmentAuthority, 'id'>

export interface FormFillInput {
  projectId: string
  context: Record<string, string>
  title?: string
}

/**
 * Fetch all government forms from backend API
 */
async function getForms(): Promise<GovernmentForm[]> {
  try {
    return await apiClient.get<GovernmentForm[]>('/api/government/forms')
  } catch (error) {
    console.error('Failed to fetch government forms:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch forms')
  }
}

/**
 * Fetch all government authorities from backend API
 */
async function getAuthorities(): Promise<GovernmentAuthority[]> {
  try {
    return await apiClient.get<GovernmentAuthority[]>('/api/government/authorities')
  } catch (error) {
    console.error('Failed to fetch government authorities:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch authorities')
  }
}

/**
 * Create a new government form via backend API
 */
async function createForm(input: FormInput): Promise<GovernmentForm> {
  try {
    return await apiClient.post<GovernmentForm>('/api/government/forms', input)
  } catch (error) {
    console.error('Failed to create form:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create form')
  }
}

/**
 * Update a government form via backend API
 */
async function updateForm(formId: string, input: FormInput): Promise<GovernmentForm> {
  try {
    return await apiClient.patch<GovernmentForm>(`/api/government/forms/${formId}`, input)
  } catch (error) {
    console.error(`Failed to update form ${formId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update form')
  }
}

/**
 * Delete a government form via backend API
 */
async function deleteForm(formId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/government/forms/${formId}`)
  } catch (error) {
    console.error(`Failed to delete form ${formId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete form')
  }
}

/**
 * Fill in a form's {{token}} template with real project data and save
 * the rendered result as a PDF Project Document (type "Government
 * Agreement") under the given project. The real, DB-backed counterpart
 * to FormTemplatePreviewDialog.vue's on-screen-only preview.
 */
async function fillForm(formId: string, input: FormFillInput): Promise<ProjectDocument> {
  try {
    return await apiClient.post<ProjectDocument>(`/api/government/forms/${formId}/fill`, input)
  } catch (error) {
    console.error(`Failed to fill form ${formId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fill and save the form')
  }
}

/**
 * Render a form's {{token}} template with the given context straight to
 * a downloadable PDF -- nothing saved, no project needed. The admin-
 * facing counterpart to fillForm above (which requires a project and
 * saves a Document there); this is for trying a template out from
 * Administration > Documents > Government Forms. Raw fetch + blob, same pattern as
 * documentService.downloadDocument, since apiClient only parses JSON.
 */
async function renderPdf(formId: string, input: { context: Record<string, string>; title?: string }): Promise<Blob> {
  const authStore = useAuthStore()

  const doRequest = () =>
    fetch(`/api/government/forms/${formId}/render-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : {}),
      },
      credentials: 'include',
      body: JSON.stringify(input),
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }

    if (!response.ok) {
      throw new Error(`PDF generation failed with status ${response.status}`)
    }

    return await response.blob()
  } catch (error) {
    console.error(`Failed to render PDF for form ${formId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to generate PDF')
  }
}

/**
 * Attach an uploaded reference copy of the real government form (not
 * parsed -- just an attachment admin can check the template/fields
 * against). Raw fetch since this is a multipart upload, same pattern as
 * every other file upload in this codebase (see e.g. documentService).
 */
async function uploadSampleFile(formId: string, file: File): Promise<GovernmentForm> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)

  const doRequest = () =>
    fetch(`/api/government/forms/${formId}/sample-file`, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`)
    }
    return (await response.json()) as GovernmentForm
  } catch (error) {
    console.error(`Failed to upload sample file for form ${formId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload sample file')
  }
}

/**
 * Set/update government form status via backend API
 */
async function setFormStatus(formId: string, status: GovernmentForm['status']): Promise<GovernmentForm> {
  try {
    return await apiClient.patch<GovernmentForm>(`/api/government/forms/${formId}/status`, { status })
  } catch (error) {
    console.error(`Failed to update form status:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update status')
  }
}

/**
 * Create a new government authority via backend API
 */
async function createAuthority(input: AuthorityInput): Promise<GovernmentAuthority> {
  try {
    return await apiClient.post<GovernmentAuthority>('/api/government/authorities', input)
  } catch (error) {
    console.error('Failed to create authority:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create authority')
  }
}

/**
 * Update a government authority via backend API
 */
async function updateAuthority(authorityId: string, input: AuthorityInput): Promise<GovernmentAuthority> {
  try {
    return await apiClient.patch<GovernmentAuthority>(`/api/government/authorities/${authorityId}`, input)
  } catch (error) {
    console.error(`Failed to update authority ${authorityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update authority')
  }
}

/**
 * Delete a government authority via backend API
 */
async function deleteAuthority(authorityId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/government/authorities/${authorityId}`)
  } catch (error) {
    console.error(`Failed to delete authority ${authorityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete authority')
  }
}

export const governmentFormService = {
  getForms,
  getAuthorities,
  createForm,
  updateForm,
  deleteForm,
  fillForm,
  renderPdf,
  uploadSampleFile,
  setFormStatus,
  createAuthority,
  updateAuthority,
  deleteAuthority,
}
