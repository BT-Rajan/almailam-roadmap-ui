export type SubmissionStatus =
  | 'Draft'
  | 'Submitted'
  | 'Under Review'
  | 'Comments Received'
  | 'Approved'
  | 'Rejected'
  | 'Withdrawn'

export type RequiredDocumentStatus = 'Pending' | 'Uploaded' | 'Verified'

export type ResponseOutcome = 'Approved' | 'Rejected' | 'No Response'

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
  createdBy: string
  createdAt: string
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
  allDocumentsSatisfied: boolean
  proofOfSubmission?: ProofOfFile | null
  proofOfResponse?: ProofOfFile | null
  responseOutcome?: ResponseOutcome | null
}
