// A Permit Application's own workspace -- 4 stages (see
// backend/app/models/government.py's GovernmentSubmission docstring and
// core/status_transitions.py's SUBMISSION_ALLOWED_TRANSITIONS):
// Prepare (pick the authority/form, fill it in, get the required
// documents ready) -> Apply (file it, record the authority's
// acknowledgement) -> Track (log contact made while it's under review,
// including any document the authority asks for) -> Close (final
// outcome, permit/decision document, closing notes). Close is
// reachable from every stage, not only Track.
export type SubmissionStage = 'Prepare' | 'Apply' | 'Track' | 'Close'

// What the workspace's stepper shows: Overview (application details --
// a UI-only first step, not a backend stage) followed by the 4 real
// stages above, so 5 steps in all.
export type SubmissionWorkspaceTab = 'Overview' | SubmissionStage

export type RequiredDocumentStatus = 'Pending' | 'Uploaded' | 'Verified'

// The final outcome recorded when an application reaches Close --
// 'Withdrawn' covers pulling the application before a decision came
// back (there's no separate stage for that anymore).
export type ResponseOutcome = 'Approved' | 'Rejected' | 'No Response' | 'Withdrawn'

export interface SubmissionDocument {
  id: number
  name: string
  status: RequiredDocumentStatus
  originalFilename?: string | null
  fileSizeLabel?: string | null
  uploadDate?: string | null
  uploadedBy?: string | null
}

export interface ProofOfFile {
  originalFilename: string
  fileSizeLabel: string
  uploadDate: string
  uploadedBy: string
}

export interface SubmissionFollowup {
  id: string
  followupDate: string
  followupTime: string
  contactPerson: string
  notes?: string | null
  document?: ProofOfFile | null
  createdBy: string
  createdAt: string
}

export interface GovernmentSubmission {
  id: string
  projectId: string
  authorityId: string
  formId: string
  submissionNo: string
  stage: SubmissionStage
  // Set once every required document is Uploaded/Verified and staff
  // explicitly confirm the application is ready to file (Prepare -> Apply).
  readinessConfirmedAt?: string | null
  // The authority's acknowledgement of receipt, recorded together with
  // the acknowledgement document (Apply -> Track).
  acknowledgementNumber?: string | null
  paymentReference?: string | null
  submittedDate?: string | null
  expectedDecisionDate?: string | null
  decisionDate?: string | null
  documents: SubmissionDocument[]
  notes?: string | null
  closingNotes?: string | null
  allDocumentsSatisfied: boolean
  // The acknowledgement document uploaded when the application was filed.
  proofOfSubmission?: ProofOfFile | null
  // The issued permit or the authority's decision letter, uploaded at Close.
  proofOfResponse?: ProofOfFile | null
  responseOutcome?: ResponseOutcome | null
  // The planned permit (Project.selectedPermits) this application is
  // fulfilling, if any -- a submission can still be filed ad hoc with
  // no such link.
  selectedPermitId?: string | null
}
