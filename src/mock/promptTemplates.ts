import type { PromptTemplate } from '@/types/AiConfig'

export const PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: 'TPL-001',
    name: 'Project Summary',
    description: 'Summarizes current project status, risks and next steps for internal review.',
    module: 'Projects',
    template:
      'Summarize the current status of this engineering consultancy project. Highlight progress, upcoming milestones, risks and any delays. Suggest next steps.',
  },
  {
    id: 'TPL-002',
    name: 'Document Field Extraction',
    description: 'Extracts key fields from an uploaded document and flags missing information.',
    module: 'Documents',
    template:
      'Read the attached document and extract the key fields relevant to this project type. Note the confidence of each extracted field and flag anything that appears missing or inconsistent.',
  },
  {
    id: 'TPL-003',
    name: 'Contract Summary',
    description: 'Summarizes a draft or signed contract, highlighting obligations and risks.',
    module: 'Contracts',
    template:
      'Summarize the attached engineering consultancy contract. Highlight obligations, payment terms, liabilities, risks and any missing clauses.',
  },
  {
    id: 'TPL-004',
    name: 'Government Form Explanation',
    description: 'Explains a government form, its fields and commonly required supporting documents.',
    module: 'Government Forms',
    template:
      'Explain the purpose of this government form in plain language. Describe what each field is asking for, list the commonly required supporting documents and highlight common mistakes applicants make.',
  },
  {
    id: 'TPL-005',
    name: 'Customer Update',
    description: 'Drafts a client-facing progress update for a project.',
    module: 'Customer Communication',
    template:
      'Draft a short, professional progress update for the client describing what has been completed, what is currently in progress and what is expected next. Keep the tone reassuring and factual.',
  },
  {
    id: 'TPL-006',
    name: 'Executive Report Summary',
    description: 'Generates an executive summary for firm-wide performance reports.',
    module: 'Reports',
    template:
      'Generate a concise executive summary for this report. Highlight the most important trends, outliers and recommended areas of focus for leadership.',
  },
]
