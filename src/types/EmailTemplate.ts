// One of the app's fixed, non-creatable/deletable automated-email keys
// -- mirrors backend/app/models/email_template.py's EMAIL_TEMPLATE_KEYS.
// The five *_otp keys that used to live here were removed once every
// OTP-code confirmation flow switched to a signed-document upload (see
// migration 0080).
export type EmailTemplateKey =
  | 'client_welcome'
  | 'project_created'
  | 'requirement_confirmed'
  | 'quotation_approved'
  | 'contract_signed'
  | 'permit_application_submitted'
  | 'permit_response_received'
  | 'payment_received'
  | 'payment_reminder'

export interface EmailTemplate {
  key: EmailTemplateKey
  subject: string
  body: string
  updatedBy: string
  updatedAt: string
}

// One entry from the backend's merge-field catalog (see
// email_template_service.MERGE_FIELD_CATALOG) -- the available
// {{ field }} tokens for one template key.
export interface EmailMergeField {
  key: string
  label: string
}
