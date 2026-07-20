import { GOVERNMENT_AUTHORITIES } from '@/mock/governmentAuthorities'
import { GOVERNMENT_FORMS } from '@/mock/governmentForms'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getForms(): Promise<GovernmentForm[]> {
  await simulateNetworkDelay()
  return [...GOVERNMENT_FORMS]
}

async function getAuthorities(): Promise<GovernmentAuthority[]> {
  await simulateNetworkDelay()
  return [...GOVERNMENT_AUTHORITIES]
}

export type FormInput = Omit<GovernmentForm, 'id'>
export type AuthorityInput = Omit<GovernmentAuthority, 'id'>

function nextId(prefix: string, existing: { id: string }[]): string {
  const sequence = existing.length + 1
  return `${prefix}-${String(sequence).padStart(3, '0')}`
}

async function createForm(input: FormInput): Promise<GovernmentForm> {
  await simulateNetworkDelay()
  const form: GovernmentForm = { ...input, id: nextId('FORM', GOVERNMENT_FORMS) }
  GOVERNMENT_FORMS.push(form)
  return form
}

async function updateForm(formId: string, input: FormInput): Promise<GovernmentForm> {
  await simulateNetworkDelay()
  const index = GOVERNMENT_FORMS.findIndex((form) => form.id === formId)
  if (index === -1) throw new Error(`Form ${formId} not found`)
  GOVERNMENT_FORMS[index] = { ...input, id: formId }
  return GOVERNMENT_FORMS[index]
}

async function deleteForm(formId: string): Promise<void> {
  await simulateNetworkDelay()
  const index = GOVERNMENT_FORMS.findIndex((form) => form.id === formId)
  if (index !== -1) GOVERNMENT_FORMS.splice(index, 1)
}

async function setFormStatus(formId: string, status: GovernmentForm['status']): Promise<GovernmentForm> {
  await simulateNetworkDelay()
  const index = GOVERNMENT_FORMS.findIndex((form) => form.id === formId)
  if (index === -1) throw new Error(`Form ${formId} not found`)
  GOVERNMENT_FORMS[index] = { ...GOVERNMENT_FORMS[index], status }
  return GOVERNMENT_FORMS[index]
}

async function createAuthority(input: AuthorityInput): Promise<GovernmentAuthority> {
  await simulateNetworkDelay()
  const authority: GovernmentAuthority = { ...input, id: nextId('AUTH', GOVERNMENT_AUTHORITIES) }
  GOVERNMENT_AUTHORITIES.push(authority)
  return authority
}

async function updateAuthority(authorityId: string, input: AuthorityInput): Promise<GovernmentAuthority> {
  await simulateNetworkDelay()
  const index = GOVERNMENT_AUTHORITIES.findIndex((authority) => authority.id === authorityId)
  if (index === -1) throw new Error(`Authority ${authorityId} not found`)
  GOVERNMENT_AUTHORITIES[index] = { ...input, id: authorityId }
  return GOVERNMENT_AUTHORITIES[index]
}

async function deleteAuthority(authorityId: string): Promise<void> {
  await simulateNetworkDelay()
  const index = GOVERNMENT_AUTHORITIES.findIndex((authority) => authority.id === authorityId)
  if (index !== -1) GOVERNMENT_AUTHORITIES.splice(index, 1)
  const relatedForms = GOVERNMENT_FORMS.filter((form) => form.authorityId === authorityId)
  relatedForms.forEach((form) => {
    const formIndex = GOVERNMENT_FORMS.findIndex((item) => item.id === form.id)
    if (formIndex !== -1) GOVERNMENT_FORMS.splice(formIndex, 1)
  })
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
