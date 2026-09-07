import { apiClient } from '@/services/httpClient'
import type { EmailMergeField, EmailTemplate, EmailTemplateKey } from '@/types/EmailTemplate'

async function getTemplates(): Promise<EmailTemplate[]> {
  try {
    return await apiClient.get<EmailTemplate[]>('/api/email-templates')
  } catch (error) {
    console.error('Failed to fetch email templates:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch email templates')
  }
}

/** The reference panel's contents for one template key. */
async function getMergeFields(key: EmailTemplateKey): Promise<EmailMergeField[]> {
  return apiClient.get<EmailMergeField[]>(`/api/email-templates/${key}/merge-fields`)
}

async function updateTemplate(key: EmailTemplateKey, subject: string, body: string): Promise<EmailTemplate> {
  try {
    return await apiClient.patch<EmailTemplate>(`/api/email-templates/${key}`, { subject, body })
  } catch (error) {
    console.error(`Failed to update email template ${key}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update email template')
  }
}

export const emailTemplateService = {
  getTemplates,
  getMergeFields,
  updateTemplate,
}
