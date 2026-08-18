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
