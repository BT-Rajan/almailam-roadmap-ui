import { reactive } from 'vue'
import type { LoginFormData } from '@/utils/sessionClear'
import { getDefaultLoginFormData, clearCompleteSession, clearTokens, clearUserInfo } from '@/utils/sessionClear'

/**
 * Composable for managing login form state and clearing operations
 *
 * Usage:
 * ```typescript
 * const { form, clearForm, clearSession, clearAll } = useLoginFormClear()
 * ```
 */
export function useLoginFormClear() {
  const form = reactive<LoginFormData>(getDefaultLoginFormData())

  /**
   * Clear only the form fields
   */
  const clearForm = (): void => {
    form.userId = ''
    form.password = ''
    form.rememberMe = false
  }

  /**
   * Clear login session (tokens and user info)
   */
  const clearSession = (): void => {
    clearTokens()
    clearUserInfo()
  }

  /**
   * Clear everything: form, session, and tokens
   */
  const clearAll = (): void => {
    clearForm()
    clearCompleteSession({
      tokens: true,
      userInfo: true,
      allLocalStorage: false,
    })
  }

  /**
   * Reset to initial state
   */
  const reset = (): void => {
    clearAll()
  }

  return {
    form,
    clearForm,
    clearSession,
    clearAll,
    reset,
  }
}
