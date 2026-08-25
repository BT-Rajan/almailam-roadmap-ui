// The 5 stages of the Project Approval Process -- the external
// sign-off gates (Documents Signed, MEW Approval, etc.), each closed
// out by uploading its review document. Not to be confused with the 7
// project workflow stages (see WORKFLOW_STAGES in projectHelpers.ts) --
// execution activities are tagged to one of those instead (see
// ExecutionStepEditor.vue), not to these.
export interface ProcessStageDefinition {
  key: string
  label: string
  sequenceNumber: number
}

export const PROCESS_STAGES: ProcessStageDefinition[] = [
  { key: 'documents_signed', label: 'Documents Signed', sequenceNumber: 1 },
  { key: 'mew_approval', label: 'MEW Approval', sequenceNumber: 2 },
  { key: 'architectural_approval', label: 'Architectural Design Approved by Client', sequenceNumber: 3 },
  { key: 'submit_baladia_kfd', label: 'Submit to Baladia or KFD', sequenceNumber: 4 },
  { key: 'permit_approved', label: 'Permit Approved', sequenceNumber: 5 },
]

// The 3 of the 5 gates above that represent an actual government
// authority's own sign-off, not a contract milestone (Documents Signed)
// or the client's own sign-off (Architectural Design Approved by
// Client) -- the only ones a GovernmentSubmission can be tagged to (see
// backend's GOVERNMENT_SUBMISSION_STAGE_KEYS). Once a tagged submission
// is Approved, this is the gate it closes automatically.
export const GOVERNMENT_SUBMISSION_STAGE_OPTIONS = PROCESS_STAGES.filter((stage) =>
  ['mew_approval', 'submit_baladia_kfd', 'permit_approved'].includes(stage.key),
)
