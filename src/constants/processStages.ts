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
