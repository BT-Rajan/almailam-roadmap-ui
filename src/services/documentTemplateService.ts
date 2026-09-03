import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/httpClient'
import type { DocumentTemplate, DocumentTemplateType, MergeField, TemplateBlock, TemplateLayout } from '@/types/DocumentTemplate'

async function getTemplates(documentType?: DocumentTemplateType): Promise<DocumentTemplate[]> {
  try {
    const query = documentType ? `?documentType=${documentType}` : ''
    return await apiClient.get<DocumentTemplate[]>(`/api/document-templates${query}`)
  } catch (error) {
    console.error('Failed to fetch document templates:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document templates')
  }
}

/**
 * Upload a new template. Multipart, so it goes through a raw fetch with
 * FormData rather than the JSON apiClient wrapper -- same convention as
 * documentService.uploadDocument.
 */
async function uploadTemplate(documentType: DocumentTemplateType, file: File): Promise<DocumentTemplate> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('documentType', documentType)
  formData.append('file', file)

  const doRequest = () =>
    fetch('/api/document-templates', {
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
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to upload document template:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload document template')
  }
}

/** The field-mapping palette's contents for a document type. */
async function getMergeFields(documentType: DocumentTemplateType): Promise<MergeField[]> {
  return apiClient.get<MergeField[]>(`/api/document-templates/merge-fields?documentType=${documentType}`)
}

/** The uploaded template's paragraphs/tables, as plain editable text. */
async function getTemplateLayout(templateId: string): Promise<TemplateLayout> {
  return apiClient.get<TemplateLayout>(`/api/document-templates/${templateId}/layout`)
}

/** Writes the edited/field-mapped blocks back into the template's .docx. */
async function saveTemplateMapping(templateId: string, blocks: TemplateBlock[]): Promise<DocumentTemplate> {
  return apiClient.post<DocumentTemplate>(`/api/document-templates/${templateId}/mapping`, { blocks })
}

async function setDefaultTemplate(templateId: string): Promise<DocumentTemplate> {
  try {
    return await apiClient.patch<DocumentTemplate>(`/api/document-templates/${templateId}/default`)
  } catch (error) {
    console.error('Failed to set default document template:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to set default document template')
  }
}

async function deleteTemplate(templateId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/document-templates/${templateId}`)
  } catch (error) {
    console.error('Failed to delete document template:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete document template')
  }
}

async function _downloadBlob(path: string, failureMessage: string): Promise<Blob> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch(path, {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) {
    const data = await response.json().catch(() => undefined)
    throw new Error(data?.error ?? data?.detail ?? data?.message ?? failureMessage)
  }
  return await response.blob()
}

async function downloadTemplate(templateId: string): Promise<Blob> {
  return _downloadBlob(`/api/document-templates/${templateId}/download`, 'Failed to download document template')
}

/** Downloads the merged Quotation document (the uploaded default
 * template with this quotation's live data merged in). */
async function downloadQuotationDocument(quotationNo: string): Promise<Blob> {
  return _downloadBlob(`/api/quotations/${quotationNo}/document`, 'Failed to generate quotation document')
}

/** Downloads the merged Contract document (the uploaded default
 * template with this contract's live data merged in). */
async function downloadContractDocument(contractNo: string): Promise<Blob> {
  return _downloadBlob(`/api/contracts/${contractNo}/document`, 'Failed to generate contract document')
}

/** The same merged Quotation document as downloadQuotationDocument, as a
 * PDF -- what Print opens in a new tab so it reflects the uploaded
 * template instead of the separate on-screen preview. */
async function getQuotationDocumentPdf(quotationNo: string): Promise<Blob> {
  return _downloadBlob(`/api/quotations/${quotationNo}/document/pdf`, 'Failed to generate quotation PDF')
}

/** PDF counterpart of downloadContractDocument -- see
 * getQuotationDocumentPdf. */
async function getContractDocumentPdf(contractNo: string): Promise<Blob> {
  return _downloadBlob(`/api/contracts/${contractNo}/document/pdf`, 'Failed to generate contract PDF')
}

/** Emails the merged Quotation PDF to the project's client (or an
 * override address) -- same merged template as Download/Print. */
async function emailQuotationDocument(quotationNo: string, toEmail?: string): Promise<void> {
  try {
    await apiClient.post(`/api/quotations/${quotationNo}/document/email`, toEmail ? { toEmail } : {})
  } catch (error) {
    console.error(`Failed to email quotation ${quotationNo}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to email quotation')
  }
}

/** Emails the merged Contract PDF -- see emailQuotationDocument. */
async function emailContractDocument(contractNo: string, toEmail?: string): Promise<void> {
  try {
    await apiClient.post(`/api/contracts/${contractNo}/document/email`, toEmail ? { toEmail } : {})
  } catch (error) {
    console.error(`Failed to email contract ${contractNo}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to email contract')
  }
}

export const documentTemplateService = {
  getTemplates,
  uploadTemplate,
  getMergeFields,
  getTemplateLayout,
  saveTemplateMapping,
  setDefaultTemplate,
  deleteTemplate,
  downloadTemplate,
  downloadQuotationDocument,
  downloadContractDocument,
  getQuotationDocumentPdf,
  getContractDocumentPdf,
  emailQuotationDocument,
  emailContractDocument,
}
