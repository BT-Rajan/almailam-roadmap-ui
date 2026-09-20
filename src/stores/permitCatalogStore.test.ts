import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { permitCatalogService } from '@/services/permitCatalogService'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import type { PermitCatalogItem } from '@/types/PermitCatalog'

vi.mock('@/services/permitCatalogService', () => ({
  permitCatalogService: { setApplicationSetup: vi.fn() },
}))

const unmapped: PermitCatalogItem = {
  id: 'PER-001', name: 'Baladia Permits', fixedCost: 0, authorityId: null, formId: null, requiredDocuments: null,
}

describe('permitCatalogStore.setApplicationSetup', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('replaces the permit with the saved setup', async () => {
    const mapped = { ...unmapped, authorityId: 'AUTH-001', formId: 'FORM-001', requiredDocuments: ['Site Plan'] }
    vi.mocked(permitCatalogService.setApplicationSetup).mockResolvedValue(mapped)
    const store = usePermitCatalogStore()
    store.permits = [unmapped]
    await store.setApplicationSetup('PER-001', { authorityId: 'AUTH-001', formId: 'FORM-001', requiredDocuments: ['Site Plan'] })
    expect(store.permits[0]).toEqual(mapped)
    expect(store.mutationError).toBeUndefined()
  })

  it('keeps the permit unchanged and reports the backend message on failure', async () => {
    vi.mocked(permitCatalogService.setApplicationSetup).mockRejectedValue(new Error('That form belongs to a different authority.'))
    const store = usePermitCatalogStore()
    store.permits = [unmapped]
    await store.setApplicationSetup('PER-001', { authorityId: 'AUTH-002', formId: 'FORM-001', requiredDocuments: null })
    expect(store.permits[0]).toEqual(unmapped)
    expect(store.mutationError).toBe('That form belongs to a different authority.')
  })
})
