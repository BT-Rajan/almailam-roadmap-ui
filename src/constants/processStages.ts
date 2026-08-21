// The 5 stages of the Project Approval Process. This is the one place
// the 5 stage names/keys/order are defined on the frontend -- every
// execution step's stageKey (see types/ExecutionStep.ts) is one of
// these keys, and ProjectProcessTab.vue groups both checklists under
// this same list so the UI shows one unified process view.
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
