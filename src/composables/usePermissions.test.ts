import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { usePermissions } from '@/composables/usePermissions'
import type { CurrentUser } from '@/services/authService'
import { useAuthStore } from '@/stores/authStore'
import { PERMISSIONS_BY_ROLE, testUser } from '@/test-utils/mockApi'

function signInAs(user: CurrentUser | null) {
  useAuthStore().$patch({ accessToken: user ? 'token' : null, user, hasHydrated: true })
}

describe('usePermissions', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('reads the flags the server sent for the signed-in user', () => {
    signInAs(testUser('Engineer'))
    const { can } = usePermissions()
    expect(can('Projects', 'edit')).toBe(true)
    expect(can('Projects', 'delete')).toBe(false)
    expect(can('Finance', 'view')).toBe(true)
    expect(can('Administration', 'view')).toBe(false)
  })

  it('follows the server-sent flags, not the role name (admins can edit the matrix)', () => {
    // A Viewer an administrator has since granted Projects:edit.
    const granted = { ...PERMISSIONS_BY_ROLE.Viewer, Projects: { view: true, edit: true, delete: false } }
    signInAs(testUser('Viewer', granted))
    expect(usePermissions().can('Projects', 'edit')).toBe(true)
  })

  it('fails closed when nobody is signed in', () => {
    signInAs(null)
    expect(usePermissions().can('Projects', 'view')).toBe(false)
  })

  it('fails closed when the user has no permissions payload at all', () => {
    signInAs(testUser('Administrator', null))
    const { can } = usePermissions()
    expect(can('Projects', 'view')).toBe(false)
    expect(can('Projects', 'edit')).toBe(false)
  })

  it('fails closed for a module the server did not report', () => {
    signInAs(testUser('Administrator', { Projects: { view: true, edit: true, delete: true } }))
    expect(usePermissions().can('Finance', 'view')).toBe(false)
  })
})
