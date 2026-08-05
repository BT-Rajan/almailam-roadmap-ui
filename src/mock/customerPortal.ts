import type {
  CustomerProjectStatus,
  ProjectDeliverable,
  ProjectMilestone,
  ProjectUpdate,
} from '@/types/CustomerPortal'

export const CUSTOMER_PORTAL_PROJECTS: Record<string, CustomerProjectStatus> = {
  'PROJ-2024-001': {
    projectId: 'PROJ-2024-001',
    projectName: 'Metro Rail Phase 2 Expansion',
    description: 'Design, planning, and execution of phase 2 expansion for metropolitan rail network',
    clientName: 'Municipal Transport Authority',
    startDate: '2024-01-15',
    expectedEndDate: '2024-12-31',
    status: 'active',
    progress: 65,
    summary:
      'Phase 2 is progressing well with most design approvals received. Infrastructure construction has commenced on 3 out of 5 sections. We are on track for the planned milestones.',
  },
  'PROJ-2024-002': {
    projectId: 'PROJ-2024-002',
    projectName: 'Highway Expansion & Modernization',
    description: 'Expansion and modernization of NH-44 highway corridor',
    clientName: 'State Transport Department',
    startDate: '2024-02-01',
    expectedEndDate: '2024-11-30',
    status: 'active',
    progress: 45,
    summary:
      'Survey and planning phase completed successfully. Environmental clearances obtained. Ready to commence construction activities in Q3.',
  },
  'PROJ-2024-003': {
    projectId: 'PROJ-2024-003',
    projectName: 'Water Treatment Plant Development',
    description: 'Construction and commissioning of water treatment facility',
    clientName: 'Municipal Authority',
    startDate: '2023-11-01',
    expectedEndDate: '2024-10-31',
    actualEndDate: '2024-10-20',
    status: 'completed',
    progress: 100,
    summary:
      'Project successfully completed ahead of schedule. All systems tested and operational. Facility is now processing water at full capacity.',
  },
}

export const CUSTOMER_PORTAL_MILESTONES: Record<string, ProjectMilestone[]> = {
  'PROJ-2024-001': [
    {
      id: 'm1',
      title: 'Design Approval',
      description: 'Obtain all necessary design approvals from stakeholders',
      dueDate: '2024-03-31',
      status: 'completed',
      completedDate: '2024-03-25',
    },
    {
      id: 'm2',
      title: 'Environmental Clearance',
      description: 'Secure environmental impact assessment and clearance',
      dueDate: '2024-05-31',
      status: 'completed',
      completedDate: '2024-05-20',
    },
    {
      id: 'm3',
      title: 'Construction Phase 1',
      description: 'Complete foundation and initial infrastructure work',
      dueDate: '2024-09-30',
      status: 'in-progress',
    },
    {
      id: 'm4',
      title: 'Construction Phase 2',
      description: 'Complete structural and systems installation',
      dueDate: '2024-12-31',
      status: 'pending',
    },
  ],
  'PROJ-2024-002': [
    {
      id: 'm1',
      title: 'Survey & Assessment',
      dueDate: '2024-04-30',
      status: 'completed',
      completedDate: '2024-04-15',
    },
    {
      id: 'm2',
      title: 'Environmental Clearance',
      dueDate: '2024-06-30',
      status: 'in-progress',
    },
    {
      id: 'm3',
      title: 'Land Acquisition',
      dueDate: '2024-09-30',
      status: 'pending',
    },
  ],
  'PROJ-2024-003': [
    {
      id: 'm1',
      title: 'Site Preparation',
      dueDate: '2024-01-31',
      status: 'completed',
      completedDate: '2024-01-20',
    },
    {
      id: 'm2',
      title: 'Construction',
      dueDate: '2024-08-31',
      status: 'completed',
      completedDate: '2024-08-25',
    },
    {
      id: 'm3',
      title: 'Testing & Commissioning',
      dueDate: '2024-10-31',
      status: 'completed',
      completedDate: '2024-10-20',
    },
  ],
}

export const CUSTOMER_PORTAL_DELIVERABLES: Record<string, ProjectDeliverable[]> = {
  'PROJ-2024-001': [
    {
      id: 'd1',
      name: 'Design Documentation',
      description: 'Complete design and technical specifications',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2024-03-20',
      approvalDate: '2024-03-25',
    },
    {
      id: 'd2',
      name: 'Safety Plan',
      description: 'Comprehensive safety and risk management plan',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2024-04-10',
      approvalDate: '2024-04-15',
    },
    {
      id: 'd3',
      name: 'Progress Report Q2',
      description: 'Second quarter progress and status report',
      type: 'PDF',
      status: 'delivered',
      deliveryDate: '2024-06-30',
    },
    {
      id: 'd4',
      name: 'Progress Report Q3',
      description: 'Third quarter progress and status report',
      type: 'PDF',
      status: 'pending',
    },
  ],
  'PROJ-2024-002': [
    {
      id: 'd1',
      name: 'Survey Report',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2024-04-20',
      approvalDate: '2024-04-25',
    },
    {
      id: 'd2',
      name: 'Environmental Impact Assessment',
      type: 'PDF',
      status: 'delivered',
      deliveryDate: '2024-06-15',
    },
  ],
  'PROJ-2024-003': [
    {
      id: 'd1',
      name: 'Design & Specifications',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2023-12-15',
      approvalDate: '2023-12-20',
    },
    {
      id: 'd2',
      name: 'Construction Progress Reports',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2024-09-30',
      approvalDate: '2024-10-01',
    },
    {
      id: 'd3',
      name: 'As-Built Documentation',
      type: 'PDF',
      status: 'approved',
      deliveryDate: '2024-10-20',
      approvalDate: '2024-10-20',
    },
  ],
}

export const CUSTOMER_PORTAL_UPDATES: Record<string, ProjectUpdate[]> = {
  'PROJ-2024-001': [
    {
      id: 'u1',
      date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Section 3 Construction Commenced',
      description: 'Construction activities for section 3 have officially started with site mobilization complete.',
      type: 'status',
    },
    {
      id: 'u2',
      date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Progress Report Q3 Published',
      description: 'Quarterly progress report for Q3 is now available in deliverables.',
      type: 'deliverable',
    },
    {
      id: 'u3',
      date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Construction Phase 1 Milestone Achieved',
      description: 'All foundation work for phase 1 successfully completed on schedule.',
      type: 'milestone',
    },
  ],
  'PROJ-2024-002': [
    {
      id: 'u1',
      date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Environmental Clearance In Progress',
      description: 'Environmental impact assessment review is underway with authorities.',
      type: 'status',
    },
  ],
  'PROJ-2024-003': [
    {
      id: 'u1',
      date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Project Successfully Completed',
      description: 'All project objectives achieved and facility is operational.',
      type: 'milestone',
    },
  ],
}
