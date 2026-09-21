import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/httpClient'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import { useAuditLogStore } from '@/stores/auditLogStore'
import { useClientStore } from '@/stores/clientStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useDocumentTemplateStore } from '@/stores/documentTemplateStore'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useMessageCentreStore } from '@/stores/messageCentreStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useProjectFormStore } from '@/stores/projectFormStore'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useSitePortalStore } from '@/stores/sitePortalStore'
import { useStatusReportStore } from '@/stores/statusReportStore'
import { useTaskStore } from '@/stores/taskStore'
import { useUserStore } from '@/stores/userStore'
import { overrideMockApi, resetMockApi } from '@/test-utils/mockApi'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

/**
 * Every store that used to answer any failure with one fixed sentence.
 *
 * Each case makes every API call fail with a 429 and checks the store's error
 * field says so. That exercises the store AND the service under it: it fails
 * if a service flattens the ApiError into a bare Error (status lost) just as
 * surely as if the store swallows it -- which is exactly how a rate-limit
 * loop hid behind "Unable to load contracts. Please try again." in production.
 *
 * Deliberately not listed (they already show error.message, or ignore
 * failure on purpose): mutationError/askError fields, audit-event history,
 * branding, server-time, auth token clean-up, optimistic mark-as-read.
 */
const CASES: [name: string, run: () => Promise<string | undefined>][] = [
  ['aiConfigStore.loadConfiguration', async () => { const s = useAIConfigStore(); await s.loadConfiguration(); return s.error }],
  // The two save actions return early unless data is already loaded, so seed it -- otherwise no request is made and there is nothing to fail.
  ['aiConfigStore.saveConfiguration', async () => { const s = useAIConfigStore(); s.config = {} as never; await s.saveConfiguration(); return s.error }],
  ['auditLogStore.loadLogs', async () => { const s = useAuditLogStore(); await s.loadLogs(); return s.error }],
  ['clientStore.loadClients', async () => { const s = useClientStore(); await s.loadClients(); return s.error }],
  ['clientStore.loadClientsPage', async () => { const s = useClientStore(); await s.loadClientsPage(); return s.error }],
  ['clientStore.loadClientDetail', async () => { const s = useClientStore(); await s.loadClientDetail('CL-1'); return s.detailError }],
  ['companyStore.loadSettings', async () => { const s = useCompanyStore(); await s.loadSettings(); return s.error }],
  ['companyStore.saveSettings', async () => { const s = useCompanyStore(); s.settings = {} as never; await s.saveSettings(); return s.error }],
  ['contractStore.loadContractsForProject', async () => { const s = useContractStore(); await s.loadContractsForProject('P-1'); return s.error }],
  ['documentStore.loadDocuments', async () => { const s = useDocumentStore(); await s.loadDocuments(); return s.error }],
  ['documentStore.loadDocumentsForProject', async () => { const s = useDocumentStore(); await s.loadDocumentsForProject('P-1'); return s.error }],
  ['documentStore.loadDocumentsPage', async () => { const s = useDocumentStore(); await s.loadDocumentsPage(); return s.error }],
  ['documentStore.loadDocumentDetail', async () => { const s = useDocumentStore(); await s.loadDocumentDetail('DOC-1'); return s.error }],
  ['documentTemplateStore.loadTemplates', async () => { const s = useDocumentTemplateStore(); await s.loadTemplates(); return s.error }],
  ['governmentFormStore.loadForms', async () => { const s = useGovernmentFormStore(); await s.loadForms(); return s.error }],
  ['governmentSubmissionStore.loadSubmissions', async () => { const s = useGovernmentSubmissionStore(); await s.loadSubmissions(); return s.error }],
  ['governmentSubmissionStore.loadSubmissionsForProject', async () => { const s = useGovernmentSubmissionStore(); await s.loadSubmissionsForProject('P-1'); return s.error }],
  ['knowledgeStore.loadDocuments', async () => { const s = useKnowledgeStore(); await s.loadDocuments(); return s.error }],
  ['messageCentreStore.loadAll', async () => { const s = useMessageCentreStore(); await s.loadAll(); return s.error }],
  ['notificationStore.loadNotifications', async () => { const s = useNotificationStore(); await s.loadNotifications(); return s.error }],
  ['paymentStore.loadAll', async () => { const s = usePaymentStore(); await s.loadAll(); return s.error }],
  ['paymentStore.loadForProject', async () => { const s = usePaymentStore(); await s.loadForProject('P-1'); return s.error }],
  ['permitCatalogStore.loadPermits', async () => { const s = usePermitCatalogStore(); await s.loadPermits(); return s.error }],
  ['projectFormStore.load', async () => { const s = useProjectFormStore(); await s.load('P-1'); return s.error }],
  ['projectLinkDocumentStore.loadForProject', async () => { const s = useProjectLinkDocumentStore(); await s.loadForProject('P-1'); return s.error }],
  ['projectStore.loadProjects', async () => { const s = useProjectStore(); await s.loadProjects(); return s.error }],
  ['projectStore.loadProjectsPage', async () => { const s = useProjectStore(); await s.loadProjectsPage(); return s.error }],
  ['quotationStore.loadQuotationsForProject', async () => { const s = useQuotationStore(); await s.loadQuotationsForProject('P-1'); return s.error }],
  ['serviceCatalogStore.loadServices', async () => { const s = useServiceCatalogStore(); await s.loadServices(); return s.error }],
  ['sitePortalStore.loadCalendarRange', async () => { const s = useSitePortalStore(); await s.loadCalendarRange('2026-09-01', '2026-09-30'); return s.error }],
  ['statusReportStore.loadInbox', async () => { const s = useStatusReportStore(); await s.loadInbox(); return s.error }],
  ['statusReportStore.loadForProject', async () => { const s = useStatusReportStore(); await s.loadForProject('P-1'); return s.projectError }],
  ['statusReportStore.loadForTask', async () => { const s = useStatusReportStore(); await s.loadForTask('T-1'); return s.taskError }],
  ['taskStore.loadTasks', async () => { const s = useTaskStore(); await s.loadTasks(); return s.error }],
  ['taskStore.loadTasksForProject', async () => { const s = useTaskStore(); await s.loadTasksForProject('P-1'); return s.error }],
  ['taskStore.loadAuditEvents', async () => { const s = useTaskStore(); await s.loadAuditEvents('T-1'); return s.historyError }],
  ['userStore.loadUsers', async () => { const s = useUserStore(); await s.loadUsers(); return s.error }],
]

describe('stores report the real HTTP failure instead of one generic message', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    resetMockApi()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    overrideMockApi(/.*/, () => {
      throw new ApiError(429, 'Too many requests. Please slow down.')
    })
  })

  it.each(CASES)('%s', async (_name, run) => {
    const message = await run()
    expect(message, 'the store recorded no error at all').toBeTruthy()
    expect(message).toContain('HTTP 429')
    expect(message).toContain('Too many requests')
  })

  it('covers every store call that uses describeStoreError', () => {
    // Guards the table itself: a store site migrated later without a case here
    // would otherwise go untested.
    const sources = import.meta.glob('./*Store.ts', { query: '?raw', import: 'default', eager: true }) as Record<string, string>
    const sites = Object.values(sources).reduce((n, src) => n + (src.match(/describeStoreError\(/g)?.length ?? 0), 0)
    expect(CASES.length, 'add a case for each store site that uses describeStoreError').toBe(sites)
  })
})
