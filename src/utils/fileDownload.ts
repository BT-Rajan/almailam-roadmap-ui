/**
 * Triggers a browser "Save As" for an already-fetched Blob. Shared here
 * because this exact blob -> object URL -> anchor click -> revoke
 * sequence was starting to get duplicated inline across several stores
 * (clientStore, auditLogStore) each time a new download feature was
 * added.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

/**
 * Opens a Blob (a generated PDF, typically) in a browser tab -- for
 * "Print" actions that need to fetch the file first. `targetWindow`
 * should be the result of a `window.open('', '_blank')` called
 * synchronously inside the click handler, *before* the async fetch --
 * most browsers only allow window.open() as a direct response to a user
 * gesture, so opening it fresh only after an `await` resolves gets
 * silently popup-blocked. Falls back to window.open(url) directly
 * (works when pop-ups are otherwise allowed) if that blank window
 * wasn't available.
 */
export function openBlobInWindow(blob: Blob, targetWindow: Window | null): void {
  const url = URL.createObjectURL(blob)
  if (targetWindow) {
    targetWindow.location.href = url
  } else {
    window.open(url, '_blank')
  }
  // Revoked well after the tab has had time to load the PDF, not
  // immediately -- an immediate revoke can race the new tab's own fetch
  // of the blob: URL and leave it blank.
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
