/**
 * Session Clearing Utility
 * 
 * Provides comprehensive functions to clear login data, session information,
 * and authentication tokens from the application.
 */

export interface ClearSessionOptions {
  tokens?: boolean
  userInfo?: boolean
  formData?: boolean
  errorMessages?: boolean
  allLocalStorage?: boolean
}

/**
 * Clear specific login tokens
 */
export function clearTokens(): void {
  localStorage.removeItem('almailam-access-token')
  localStorage.removeItem('almailam-refresh-token')
}

/**
 * Clear user information
 */
export function clearUserInfo(): void {
  localStorage.removeItem('almailam-user-info')
}

/**
 * Clear all application data from localStorage
 */
export function clearAllLocalStorage(): void {
  // Get all keys that start with 'almailam-' or 'serviceos-'
  const keysToRemove = Object.keys(localStorage).filter(
    (key) => key.startsWith('almailam-') || key.startsWith('serviceos-')
  )
  keysToRemove.forEach((key) => localStorage.removeItem(key))
}

/**
 * Clear application state and cache
 */
export function clearApplicationState(): void {
  // Clear session storage
  sessionStorage.clear()

  // Clear IndexedDB if used
  if (window.indexedDB) {
    indexedDB.databases().then((dbs) => {
      dbs.forEach((db) => {
        if (db.name?.includes('almailam') || db.name?.includes('serviceos')) {
          indexedDB.deleteDatabase(db.name)
        }
      })
    })
  }
}

/**
 * Clear browser cache and cookies related to the application
 * Note: This is a client-side operation and may not clear all cookies
 */
export function clearBrowserCache(): void {
  // Clear cookies
  document.cookie.split(';').forEach((cookie) => {
    const eqPos = cookie.indexOf('=')
    const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim()
    if (name.includes('almailam') || name.includes('serviceos')) {
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`
    }
  })
}

/**
 * Complete session clear - removes all authentication and user data
 * This is what happens when user logs out
 */
export function clearCompleteSession(options: ClearSessionOptions = {}): void {
  const {
    tokens = true,
    userInfo = true,
    formData = true,
    errorMessages = true,
    allLocalStorage = false,
  } = options

  if (tokens) clearTokens()
  if (userInfo) clearUserInfo()
  if (allLocalStorage) clearAllLocalStorage()

  // Note: formData and errorMessages are handled at component level
  if (formData) {
    // Components should handle this via their own state
  }
  if (errorMessages) {
    // Components should handle this via their own state
  }
}

/**
 * Clear login form data (for use in login page)
 */
export interface LoginFormData {
  userId: string
  password: string
  rememberMe: boolean
}

export function getDefaultLoginFormData(): LoginFormData {
  return {
    userId: '',
    password: '',
    rememberMe: false,
  }
}

/**
 * Verify session is clear (for debugging)
 */
export function isSessionClear(): boolean {
  const hasAccessToken = localStorage.getItem('almailam-access-token') !== null
  const hasRefreshToken = localStorage.getItem('almailam-refresh-token') !== null
  const hasUserInfo = localStorage.getItem('almailam-user-info') !== null

  return !hasAccessToken && !hasRefreshToken && !hasUserInfo
}

/**
 * Get current session status
 */
export function getSessionStatus(): {
  isAuthenticated: boolean
  hasAccessToken: boolean
  hasRefreshToken: boolean
  hasUserInfo: boolean
  tokenKeys: string[]
} {
  const hasAccessToken = localStorage.getItem('almailam-access-token') !== null
  const hasRefreshToken = localStorage.getItem('almailam-refresh-token') !== null
  const hasUserInfo = localStorage.getItem('almailam-user-info') !== null
  const tokenKeys = Object.keys(localStorage).filter(
    (key) => key.includes('token') || key.includes('user')
  )

  return {
    isAuthenticated: hasAccessToken && hasRefreshToken,
    hasAccessToken,
    hasRefreshToken,
    hasUserInfo,
    tokenKeys,
  }
}

/**
 * Clear browser history and cache (requires user confirmation in real scenarios)
 * This is more of a utility function for testing/development
 */
export function clearBrowserHistory(): void {
  if (typeof window !== 'undefined' && window.history) {
    // This can only go back in history, not clear it completely
    // Actual history clearing requires browser-level permissions
    window.history.pushState(null, '', window.location.href)
  }
}
