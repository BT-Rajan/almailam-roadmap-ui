// Content transcribed from the Phase 1 roadmap artwork.
// Kept as data so components stay presentational.

export const phases = [
  {
    n: 1,
    title: "Client Request",
    subtitle: "Client contacts the firm",
    channels: ["WhatsApp", "Phone", "Email", "Walk-in / Website"],
  },
  {
    n: 2,
    title: "Quotation Preparation",
    subtitle: "Firm prepares quotation",
    steps: ["Select services", "AI extracts data from documents", "Generate quotation", "Review & send"],
  },
  {
    n: 3,
    title: "Contract Generation",
    subtitle: "On quotation approval",
    steps: ["AI generates contract", "Review & send", "Client signs", "Firm signs"],
  },
  {
    n: 4,
    title: "Project Creation",
    subtitle: "Project & dashboards created",
    steps: ["Project number", "Timeline & milestones", "Documents & approvals", "Dashboards for firm & client"],
  },
]

export const active = {
  title: "Project Active",
  subtitle: "Track progress until completion",
  views: [
    { label: "Firm", detail: "Full internal dashboard" },
    { label: "Client", detail: "Real-time project portal" },
  ],
}

export const aiFunctions = [
  {
    title: "AI Document Reading",
    detail: "Reads uploaded documents and extracts information.",
    items: ["Civil ID", "Ownership deed", "Survey plan", "Government letters", "Approvals"],
    flow: ["Extracted", "Verified", "Stored"],
  },
  {
    title: "AI Quotation Generation",
    detail: "Generates a quotation draft from verified data and service templates.",
    items: ["Scope of work", "Pricing", "Payment terms", "Validity"],
    flow: ["Draft", "Review", "Send"],
  },
  {
    title: "AI Contract Generation",
    detail: "Converts an approved quotation into a contract automatically.",
    items: ["Client & property info", "Selected services", "Terms & conditions", "Responsibilities"],
    flow: ["Draft", "Review", "Sign"],
  },
  {
    title: "AI Document Retrieval",
    detail: "Finds any document instantly.",
    items: ["\u201CShow client civil ID\u201D", "\u201CRetrieve signed contract\u201D", "\u201CLatest municipality comment\u201D", "\u201CDocuments awaiting client\u201D"],
    flow: ["Search", "Find", "View / download"],
  },
  {
    title: "AI Dashboard Creation",
    detail: "Creates milestones, tasks, documents & approvals based on the service template.",
    items: ["Milestones & dependencies", "Responsibilities", "Planned dates & deadlines", "Progress stages"],
    flow: ["Template", "Generate", "Track"],
  },
  {
    title: "AI Progress Answers",
    detail: "Answers status questions using verified project data.",
    items: ["Current status", "Next milestone", "Who is responsible", "Delay reasons"],
    flow: ["Ask", "AI checks data", "Answer"],
  },
]

export const serviceExamples = [
  "New building license",
  "Modification license",
  "Addition license",
  "Demolition license",
  "Renovation license",
  "Interior partitions license",
  "Change of use (invest. to apartments)",
  "Shade / car canopy license",
  "Agriculture license",
  "And other engineering services",
]

export const serviceFields = [
  { label: "Required documents", icon: "doc" },
  { label: "Government approvals", icon: "stamp" },
  { label: "Responsible parties", icon: "user" },
  { label: "Milestones & sequence", icon: "list" },
  { label: "Expected durations", icon: "clock" },
  { label: "Standard scope & wording", icon: "text" },
  { label: "Pricing & payment terms", icon: "coin" },
]

export const internalDashboard = [
  "All milestones & tasks",
  "Document status",
  "Government submissions",
  "Deadlines & delays",
  "Responsible employees",
  "Internal notes & history",
  "Full communication",
  "Reports & analytics",
]

export const clientDashboard = [
  "Overall progress",
  "Milestone timeline",
  "Current stage",
  "What\u2019s in process",
  "What\u2019s required from client",
  "Approvals status",
  "Upcoming dates",
  "Download documents",
  "Notifications & actions",
]

export const projectTimeline = [
  { label: "Contract signed", state: "done" },
  { label: "Documents verified", state: "done" },
  { label: "Design completed", state: "done" },
  { label: "Municipality submitted", state: "done" },
  { label: "Under review (municipality)", state: "active" },
  { label: "Comments received", state: "pending" },
  { label: "Resubmission", state: "pending" },
  { label: "Approved", state: "pending" },
  { label: "Permit issued", state: "pending" },
  { label: "Construction (if included)", state: "pending" },
]

export const documents = [
  { item: "Civil ID", requiredFor: "All services", responsible: "Client", status: "Uploaded", due: "10/01/2025", received: "10/01/2025", approved: "\u2013", note: "Verified" },
  { item: "Ownership deed", requiredFor: "All services", responsible: "Client", status: "Uploaded", due: "10/01/2025", received: "10/01/2025", approved: "\u2013", note: "Verified" },
  { item: "Survey plan", requiredFor: "New build, add.", responsible: "Client", status: "Pending", due: "15/01/2025", received: "\u2013", approved: "\u2013", note: "Awaiting" },
  { item: "Soil report", requiredFor: "New build", responsible: "Client", status: "Missing", due: "15/01/2025", received: "\u2013", approved: "\u2013", note: "Required" },
  { item: "Municipality approval", requiredFor: "New build", responsible: "Firm", status: "Under review", due: "\u2013", received: "25/01/2025", approved: "\u2013", note: "At Baladiya" },
  { item: "Fire force approval", requiredFor: "New build", responsible: "Firm", status: "Not started", due: "\u2013", received: "\u2013", approved: "\u2013", note: "\u2013" },
]

export const milestones = [
  "Contract signed",
  "Documents completed",
  "Design completed",
  "Internal review",
  "Municipality submission",
  "Under municipality review",
  "Comments received",
  "Corrections & resubmission",
  "Municipality approval",
  "Other authority approvals",
  "Permit issued",
  "Project completion",
]

export const benefits = [
  "Faster quotation & contract preparation",
  "No re-entry \u2014 data reused everywhere",
  "Clear responsibilities & deadlines",
  "Real-time project visibility",
  "AI reduces manual work & errors",
  "Better client experience & trust",
  "Full control & audit trail",
  "Organized knowledge & documents",
]
