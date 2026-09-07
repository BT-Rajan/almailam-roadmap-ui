// One of the app's fixed, non-creatable/deletable automated-email keys
// -- mirrors backend/app/models/email_template.py's EMAIL_TEMPLATE_KEYS.
export type EmailTemplateKey =
  | 'client_onboarding_otp'
  | 'client_welcome'
  | 'project_created'
  | 'requirement_otp'
  | 'requirement_confirmed'
  | 'quotation_otp'
  | 'quotation_approved'
  | 'contract_otp'
  | 'contract_signed'
  | 'handover_otp'
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
