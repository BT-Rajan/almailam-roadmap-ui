import { apiClient } from '@/services/httpClient'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'

export type FormInput = Omit<GovernmentForm, 'id'>
export type AuthorityInput = Omit<GovernmentAuthority, 'id'>

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
  setFormStatus,
  createAuthority,
  updateAuthority,
  deleteAuthority,
}
