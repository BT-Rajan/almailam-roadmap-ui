// crypto.randomUUID() only exists in secure contexts (HTTPS or localhost).
// This app is served over plain HTTP on some deployments, where
// crypto.randomUUID is undefined and calling it throws
// "crypto.randomUUID is not a function". crypto.getRandomValues has no such
// restriction, so it's used here as the primary path, with a Math.random
// fallback for the (very old / non-browser) case where crypto is absent.
export function uuid(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = crypto.getRandomValues(new Uint8Array(16))
    bytes[6] = (bytes[6] & 0x0f) | 0x40 // version 4
    bytes[8] = (bytes[8] & 0x3f) | 0x80 // variant 10
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  }

  // Last-resort fallback: not cryptographically strong, but fine for
  // client-side UI ids (toasts, dialog default ids) where uniqueness --
  // not unpredictability -- is what matters.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
