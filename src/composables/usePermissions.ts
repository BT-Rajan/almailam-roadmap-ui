import { computed } from 'vue'

import type { PermissionAction } from '@/services/authService'
import { useAuthStore } from '@/stores/authStore'
import type { PermissionModule } from '@/types/Role'

/**
 * Whether the signed-in user may do `action` in `module`, according to the
 * server's own role matrix (delivered on /api/auth/me).
 *
 * Prefer this over useRbac() for anything that mirrors a backend
 * require_permission(...) check. useRbac() is a hardcoded table in the
 * frontend and has already drifted from the database-driven, admin-editable
 * matrix (e.g. it says Engineers can't edit projects; the API says they can),
 * so gating on it hides buttons from people the server would allow, or shows
 * them to people it would refuse.
 *
 * Fails closed: no user, or a module the server didn't report, means no
 * access. The server still enforces every request; this only decides what
 * the UI offers.
 *
 * Note the flags are read once per session (login / page reload), so a
 * matrix edit reaches an already-signed-in user's UI on their next reload.
 * The API applies it immediately.
 */
export function usePermissions() {
  const authStore = useAuthStore()

  function can(module: PermissionModule, action: PermissionAction): boolean {
    return authStore.user?.permissions?.[module]?.[action] === true
  }

  return {
    can,
    /** Reactive helper for templates/computed: canRef('Projects', 'edit').value */
    canRef: (module: PermissionModule, action: PermissionAction) => computed(() => can(module, action)),
  }
}
