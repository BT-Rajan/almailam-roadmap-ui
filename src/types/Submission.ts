export type SubmissionStatus = 'Draft' | 'Submitted' | 'Under Review' | 'Comments Received' | 'Approved' | 'Rejected'

export type RequiredDocumentStatus = 'Pending' | 'Uploaded' | 'Verified'

export interface SubmissionDocument {
  name: string
  status: RequiredDocumentStatus
}

export interface GovernmentSubmission {
  id: string
  projectId: string
  authorityId: string
  formId: string
  submissionNo: string
  status: SubmissionStatus
  submittedDate?: string
  expectedDecisionDate?: string
  decisionDate?: string
  documents: SubmissionDocument[]
  notes?: string
}
