export type EmailProviderId = 'gmail' | 'outlook' | 'yahoo' | 'icloud' | 'custom'

export interface EmailProviderPreset {
  label: string
  smtpHost: string
  smtpPort: number
  smtpUseTls: boolean
  note: string
}

export interface EmailSettings {
  provider: EmailProviderId
  smtpHost: string
  smtpPort: number
  smtpUseTls: boolean
  username: string
  hasPassword: boolean
  fromEmail: string
  fromName: string
  isActive: boolean
  lastTestedAt: string | null
  lastTestOk: boolean | null
  lastTestError: string | null
  // True when SMTP_HOST is set in the server's .env -- that override
  // always wins over these saved settings (see backend
  // email_service._resolve_smtp_config), so the form can say so rather
  // than letting an edit here look like it silently did nothing.
  envOverrideActive: boolean
  // Write-only, local-only: a raw password just typed into the admin
  // form, staged until Save Changes is clicked. Never present in a GET
  // response -- the server never echoes back a real password. Cleared
  // after a successful save (see emailSettingsStore.saveSettings).
  password?: string
}

export interface EmailSettingsTestResult {
  ok: boolean
  message: string
}
