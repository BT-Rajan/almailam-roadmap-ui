import type { WorkflowTemplate } from '@/types/Workflow'

export const WORKFLOW_TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'WFT-001',
    name: 'Standard Project Workflow',
    isDefault: true,
    stages: [
      { id: 'STG-001', name: 'Enquiry', description: 'Initial client enquiry and scope discussion.' },
      { id: 'STG-002', name: 'Quotation', description: 'Prepare and issue the project quotation.' },
      { id: 'STG-003', name: 'Contract', description: 'Draft and sign the consultancy agreement.' },
      { id: 'STG-004', name: 'Design', description: 'Develop the engineering design deliverables.' },
      { id: 'STG-005', name: 'Government Submission', description: 'Submit design package to relevant authorities.' },
      { id: 'STG-006', name: 'Review', description: 'Authority review of the submitted package.' },
      { id: 'STG-007', name: 'Correction', description: 'Address review comments and resubmit if required.' },
      { id: 'STG-008', name: 'Approval', description: 'Final authority approval received.' },
      { id: 'STG-009', name: 'Completed', description: 'Project deliverables handed over to the client.' },
    ],
  },
  {
    id: 'WFT-002',
    name: 'Fast-Track Renovation Workflow',
    isDefault: false,
    stages: [
      { id: 'STG-101', name: 'Enquiry', description: 'Initial client enquiry and site assessment.' },
      { id: 'STG-102', name: 'Quotation', description: 'Prepare a simplified renovation quotation.' },
      { id: 'STG-103', name: 'Design', description: 'Produce renovation drawings for approval.' },
      { id: 'STG-104', name: 'Approval', description: 'Client and authority sign-off on renovation scope.' },
      { id: 'STG-105', name: 'Completed', description: 'Renovation works handed over.' },
    ],
  },
  {
    id: 'WFT-003',
    name: 'Government-Heavy Infrastructure Workflow',
    isDefault: false,
    stages: [
      { id: 'STG-201', name: 'Enquiry', description: 'Initial scoping for infrastructure works.' },
      { id: 'STG-202', name: 'Quotation', description: 'Prepare the infrastructure project quotation.' },
      { id: 'STG-203', name: 'Contract', description: 'Sign the infrastructure consultancy agreement.' },
      { id: 'STG-204', name: 'Design', description: 'Develop multi-discipline infrastructure design.' },
      { id: 'STG-205', name: 'Government Submission', description: 'Submit to municipality, fire, electricity and water authorities.' },
      { id: 'STG-206', name: 'Review', description: 'Coordinated multi-authority review.' },
      { id: 'STG-207', name: 'Correction', description: 'Resolve comments across all authorities.' },
      { id: 'STG-208', name: 'Approval', description: 'All authority approvals received.' },
      { id: 'STG-209', name: 'Completed', description: 'Infrastructure project handed over.' },
    ],
  },
]
