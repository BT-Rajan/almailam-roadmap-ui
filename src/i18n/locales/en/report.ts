export default {
  header: {
    generatedLabel: 'Generated: {date}',
    print: 'Print',
    export: 'Export',
  },

  metricCard: {
    vsLastPeriod: '{percentage}% vs last period',
  },

  back: 'Back',

  listPage: {
    pageTitle: 'Reports',
    pageSubtitle: 'Access executive summaries, project performance analytics, and team workload insights.',
    executiveTitle: 'Executive Summary Report',
    executiveDescription:
      'High-level KPIs, project status distribution, delivery trends, and resource allocation overview.',
    executiveMetric1: '{count} Active Projects',
    executiveMetric2: '{percent}% Completion Rate',
    executiveMetric3: '{percent}% Team Utilization',
    projectTitle: 'Project Performance Report',
    projectDescription:
      'Detailed analysis of a specific project including progress, budget tracking, task status, and risk assessment.',
    projectMetric2: '{percent}% Complete',
    projectMetric3: 'On Schedule',
    workloadTitle: 'Team Workload Summary',
    workloadDescription:
      'Team capacity analysis, member allocation details, department utilization, and rebalancing recommendations.',
    workloadMetric1: '{count} Team Members',
    workloadMetric2: '{percent}% Avg Utilization',
    workloadMetric3: '{percent}% Capacity Free',
    viewReport: 'View Report',
    aboutReports: 'About Reports',
    aboutExecutiveLabel: 'Executive Summary:',
    aboutExecutiveText:
      'Get a quick overview of overall organizational performance, project status, and team capacity in one comprehensive dashboard.',
    aboutProjectLabel: 'Project Performance:',
    aboutProjectText:
      'Deep-dive into specific project metrics, track progress against timelines, and identify risks early.',
    aboutWorkloadLabel: 'Team Workload:',
    aboutWorkloadText:
      'Monitor individual and department-level capacity, identify overallocation issues, and optimize resource distribution.',
    tip: 'Tip: All reports are printable and can be exported for sharing with stakeholders.',
  },

  executivePage: {
    pageTitle: 'Executive Summary Report',
    pageSubtitle: 'Current Performance Overview',
    kpiTitle: 'Key Performance Indicators',
    kpiDescription: 'High-level metrics for the current period',
    projectStatusTitle: 'Project Status Distribution',
    projectStatusDescription: 'Breakdown of projects by current status',
    paymentsTrendTitle: 'Payments Received Trend',
    paymentsTrendDescription: 'Payments received over the past 6 months',
    contractPipelineTitle: 'Contract Pipeline',
    contractPipelineDescription: 'Distribution of contracts by current status',
    footerGenerated: 'This report was automatically generated on {date}',
    footerContact: 'For questions or detailed analysis, contact the project management office.',
  },

  workloadPage: {
    pageTitle: 'Team Workload Summary',
    pageSubtitle: 'Current capacity and allocation analysis',
    teamOverviewTitle: 'Team Overview',
    teamOverviewDescription: 'High-level team capacity and utilization metrics',
    totalTeamMembers: 'Total Team Members',
    averageUtilization: 'Average Utilization',
    overallocatedStaff: 'Overallocated Staff',
    personsUnit: 'persons',
    capacityAvailable: 'Capacity Available',
    teamCapacityStatusTitle: 'Team Capacity Status',
    workloadByDisciplineTitle: 'Workload by Discipline',
    workloadByDisciplineDescription: 'Active project count by engineering discipline',
    disciplineUtilizationTitle: 'Discipline Utilization Rates',
    disciplineUtilizationDescription: 'Allocation percentage by engineering discipline',
    teamMemberDetailsTitle: 'Team Member Allocation Details',
    allocation: 'Allocation',
    projects: 'Projects',
    capacity: 'Capacity',
    overallocatedBadge: 'Overallocated',
    recommendationsTitle: 'Recommendations',
    balancedWorkloadTitle: 'Balanced Workload',
    balancedWorkloadText:
      'No engineers are currently over their capacity threshold. Structural and MEP engineering carry the highest load at 88-90% utilization.',
    hiringOpportunityTitle: 'Hiring Opportunity',
    hiringOpportunityText:
      'Fire & Safety has the lowest headcount at 68% utilization. An additional fire safety engineer would support the growing government submission workload.',
    watchListTitle: 'Watch List',
    watchListText:
      'Layla Haddad and Ahmed Rashid are each carrying two active projects. Monitor upcoming enquiries before assigning further work to either engineer.',
    footerTitle: 'Team Workload Report',
    footerGenerated: 'Generated on {date}',
    footerBasedOn: 'Based on current project assignments and team capacity data',
    disciplineStructural: 'Structural Engineering',
    disciplineMep: 'MEP Engineering',
    disciplineFireSafety: 'Fire & Safety',
    roleStructuralEngineer: 'Structural Engineer',
    roleMepEngineer: 'MEP Engineer',
    roleFireSafetyEngineer: 'Fire & Safety Engineer',
    hoursUnit: 'h',
  },

  inboxPage: {
    pageTitle: 'Status Report Inbox',
    pageSubtitle: 'Field reports awaiting review, oldest first.',
    inboxEmpty: 'Inbox is empty',
    inboxEmptyDescription: 'No status reports are waiting for review.',
    pending: 'Pending',
    attach: 'Attach',
    attachToProject: 'Attach to Project',
    task: 'Task (optional)',
    noSpecificTask: 'No specific task',
    notes: 'Notes',
    notesPlaceholder: 'Brief note for the project timeline...',
  },
}
