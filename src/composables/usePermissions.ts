import { computed } from 'vue'

import type { PermissionAction } from '@/services/authService'
import { useAuthStore } from '@/stores/authStore'
import type { PermissionModule } from '@/types/Role'

/**
 * Whether the signed-in user may do `action` in `module`, according to the
 * server's own role matrix (delivered on /api/auth/me).
 *
 * This is the only permission check in the app now -- it replaced a
 * composable (useRbac.ts, since removed) that hardcoded its own
 * role->permission table in the frontend. That table drifted from the
 * database-driven, admin-editable matrix almost immediately (e.g. it said
 * Engineers couldn't edit projects; the API said they could), so gating on
 * it hid buttons from people the server would allow, or showed them to
 * people it would refuse. Always gate on the server's own matrix instead.
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
