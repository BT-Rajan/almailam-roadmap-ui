import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ClientProjectDocumentsPanel from '@/components/client/ClientProjectDocumentsPanel.vue'
import { i18n } from '@/i18n'
import type { Project } from '@/types/Project'

const handoverDocuments = Array.from({ length: 14 }, (_, index) => ({
  id: `DOC-${index + 1}`,
  type: 'Report',
  title: `Signed Hand-over Acknowledgment ${index + 1}`,
  // Later index = newer, so DOC-14 sorts first.
  uploadDate: `2026-03-${String(index + 1).padStart(2, '0')}`,
}))

vi.mock('@/services/quotationService', () => ({
  quotationService: {
    getQuotationsByProject: vi.fn(async (projectId: string) =>
      projectId === 'P-1' ? [{ id: 'Q-1', status: 'Approved', issueDate: '2026-01-01' }] : [],
    ),
  },
}))
vi.mock('@/services/contractService', () => ({
  contractService: { getContractsByProject: vi.fn(async () => []) },
}))
vi.mock('@/services/paymentService', () => ({
  paymentService: { getAgreementByProject: vi.fn(async () => undefined) },
}))
vi.mock('@/services/documentService', () => ({
  documentService: {
    getDocumentsByProject: vi.fn(async (projectId: string) => (projectId === 'P-1' ? handoverDocuments : [])),
    downloadDocument: vi.fn(),
  },
}))
vi.mock('@/services/documentTemplateService', () => ({ documentTemplateService: {} }))

const project = (id: string, projectNo: string, projectName: string) => ({ id, projectNo, projectName }) as Project

async function mountPanel(projects: Project[]) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(ClientProjectDocumentsPanel, { props: { projects, bare: true }, global: { plugins: [pinia, i18n] } })
  await flushPromises()
  return wrapper
}

const rowsOnPage = (w: Awaited<ReturnType<typeof mountPanel>>) => w.findAll('li').length
const headings = (w: Awaited<ReturnType<typeof mountPanel>>) => w.findAll('p.uppercase').map((p) => p.text())

describe('ClientProjectDocumentsPanel pages by document', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows one page of documents, with the pager, when a project has many', async () => {
    const wrapper = await mountPanel([project('P-1', '2600001', 'Alpha')])
    // 1 signed quotation + 14 hand-over acknowledgments = 15 documents.
    expect(rowsOnPage(wrapper)).toBe(10)
    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.text()).toContain('15')
  })

  it('carries the rest onto the next page under the same project heading', async () => {
    const wrapper = await mountPanel([project('P-1', '2600001', 'Alpha')])
    await wrapper.find('button[aria-label="Go to page 2"]').trigger('click')
    expect(rowsOnPage(wrapper)).toBe(5)
    expect(headings(wrapper)).toEqual(['2600001 – Alpha'])
  })

  it('keeps a project with no documents visible, under its own heading', async () => {
    const wrapper = await mountPanel([project('P-2', '2600002', 'Beta'), project('P-1', '2600001', 'Alpha')])
    // Sorted by project number: Alpha's ten documents fill page 1, Beta follows on page 2.
    expect(headings(wrapper)).toEqual(['2600001 – Alpha'])
    await wrapper.find('button[aria-label="Go to page 2"]').trigger('click')
    expect(headings(wrapper)).toContain('2600002 – Beta')
    expect(wrapper.text()).toContain('No documents available yet.')
  })

  it('has no pager when everything fits', async () => {
    const wrapper = await mountPanel([project('P-2', '2600002', 'Beta')])
    expect(wrapper.find('nav').exists()).toBe(false)
    expect(wrapper.text()).toContain('No documents available yet.')
  })
})
