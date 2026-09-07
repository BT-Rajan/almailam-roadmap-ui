import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { CompanyBranding, CompanySettings } from '@/types/CompanySettings'

/**
 * Fetch company settings from backend API
 */
async function getCompanySettings(): Promise<CompanySettings> {
  try {
    return await apiClient.get<CompanySettings>('/api/company/settings')
  } catch (error) {
    console.error('Failed to fetch company settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch settings')
  }
}

/**
 * The narrow branding subset (brand color, name, logo flag) any logged-in
 * role can fetch, regardless of Administration permissions -- see
 * GET /api/company/branding. Used to theme the app on boot.
 */
async function getBranding(): Promise<CompanyBranding> {
  try {
    return await apiClient.get<CompanyBranding>('/api/company/branding')
  } catch (error) {
    console.error('Failed to fetch company branding:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch branding')
  }
}

/**
 * Save company settings via backend API
 */
async function saveCompanySettings(settings: CompanySettings): Promise<CompanySettings> {
  try {
    return await apiClient.post<CompanySettings>('/api/company/settings', settings)
  } catch (error) {
    console.error('Failed to save company settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to save settings')
  }
}

/**
 * Uploads (replacing any existing) the company logo, multipart -- same
 * "raw fetch with FormData" convention as documentTemplateService.
 * uploadTemplate.
 */
async function uploadLogo(file: File): Promise<CompanySettings> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)

  const doRequest = () =>
    fetch('/api/company/logo', {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()
    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }
    if (!response.ok) {
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to upload company logo:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload company logo')
  }
}

async function deleteLogo(): Promise<CompanySettings> {
  try {
    return await apiClient.delete<CompanySettings>('/api/company/logo')
  } catch (error) {
    console.error('Failed to remove company logo:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove company logo')
  }
}

/** The raw logo image, for an <img> preview -- fetched as a Blob (like
 * every other authenticated file download in this app) rather than
 * pointed at directly, since the endpoint requires an Authorization
 * header a plain <img src> can't send. */
async function getLogoBlob(): Promise<Blob> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch('/api/company/logo', {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) throw new Error('Failed to load company logo')
  return await response.blob()
}

/**
 * The company logo, fully public (no auth header needed) -- safe to
 * use directly as a plain <img src>, unlike getLogoBlob() above which
 * exists specifically because the *authenticated* /api/company/logo
 * endpoint can't be pointed at directly. Every app shell (sign-in
 * screen included, before any session exists) uses this one. 404s if
 * no logo has been uploaded -- callers should gate on
 * CompanyBranding.hasLogo (or handle the <img>'s error event) rather
 * than always rendering it.
 */
export const PUBLIC_LOGO_URL = '/api/company/branding/logo'

export const companyService = {
  getCompanySettings,
  getBranding,
  saveCompanySettings,
  uploadLogo,
  deleteLogo,
  getLogoBlob,
}
