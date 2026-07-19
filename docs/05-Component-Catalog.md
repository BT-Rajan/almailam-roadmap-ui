````md
# 05 - Component Catalog

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines every reusable Vue component used throughout the application.

Components should be generic, configurable and reusable.

Pages should compose components rather than implement UI directly.

Every component should have a single responsibility.

---

# Component Design Principles

Every component must be:

- Reusable
- Configurable through props
- Strongly typed
- Stateless where possible
- Responsive
- Accessible
- Theme aware

---

# Component Naming

Use PascalCase.

Examples

```
ProjectCard.vue

SmartTable.vue

StatusBadge.vue

WorkflowStepper.vue

GovernmentFormCard.vue
```

---

# Component Organization

```
components/

common/
navigation/
dashboard/
project/
document/
government/
task/
report/
admin/
ai/
charts/
```

---

# 1. Common Components

These components are shared across the entire application.

## Buttons

- PrimaryButton
- SecondaryButton
- GhostButton
- DangerButton
- IconButton

---

## Inputs

- TextInput
- TextArea
- NumberInput
- DatePicker
- DateRangePicker
- SelectBox
- MultiSelect
- Checkbox
- RadioGroup
- ToggleSwitch
- SearchBox

---

## Layout

- PageHeader
- PageSection
- PageToolbar
- Card
- CardHeader
- CardFooter
- Divider
- Spacer

---

## Feedback

- Loader
- SkeletonLoader
- EmptyState
- ErrorState
- Toast
- Alert
- ConfirmationDialog

---

## Display

- StatusBadge
- Avatar
- AvatarGroup
- Tag
- Chip
- ProgressBar
- CircularProgress
- MetricCard

---

# 2. Navigation Components

- Sidebar
- SidebarItem
- SidebarGroup
- TopNavigation
- UserMenu
- NotificationBell
- NotificationPanel
- Breadcrumb
- GlobalSearch
- CommandPalette

---

# 3. Data Components

## SmartTable

Features

- Search
- Filters
- Sorting
- Pagination
- Row Selection
- Bulk Actions
- Export
- Responsive

---

## FilterBar

Supports

- Search
- Dropdown Filters
- Status Filters
- Date Filters

---

## DataDisplay

- DescriptionList
- KeyValueTable
- StatisticsGrid

---

# 4. Dashboard Components

- DashboardHeader
- KPIWidget
- StatisticsCard
- QuickActionCard
- ProjectSummaryCard
- ActivityWidget
- PendingTasksWidget
- UpcomingDeadlinesWidget
- RecentDocumentsWidget
- AIInsightWidget

---

# 5. Project Components

- ProjectHeader
- ProjectCard
- ProjectSummary
- ProjectInformation
- ProjectStatusCard
- ClientInformationCard
- ProjectTimeline
- WorkflowStepper
- MilestoneCard
- ProjectActivity
- ProjectNotes
- ProjectTags

---

# 6. Document Components

- DocumentCard
- DocumentList
- DocumentViewer
- PDFViewer
- MetadataPanel
- VersionHistory
- FileUploader
- DocumentPreview
- AIReviewPanel
- OCRResultPanel

---

# 7. Government Components

- GovernmentFormCard
- GovernmentFormList
- AuthorityCard
- AuthorityDirectory
- SubmissionTimeline
- SubmissionStatusCard
- RequiredDocumentsCard
- ApprovalHistory
- ReviewComments
- CorrectionHistory

---

# 8. Task Components

- TaskCard
- TaskList
- TaskBoard
- KanbanBoard
- CalendarView
- TaskDetails
- TaskPriorityBadge
- TaskStatusBadge
- TaskAssignmentCard

---

# 9. AI Components

- AIAssistantDrawer
- AIPromptBox
- AIResponseCard
- AIHistory
- AIActionCard
- AIConfidenceBadge
- AISuggestionCard
- AILoadingState

---

# 10. Report Components

- ReportCard
- ChartCard
- KPIChart
- ProgressChart
- StatusChart
- ReportFilterBar
- ExportToolbar

---

# 11. Administration Components

- UserCard
- UserTable
- RoleCard
- PermissionMatrix
- WorkflowCard
- WorkflowStage
- WorkflowEditor
- GovernmentFormEditor
- PromptTemplateEditor
- CompanyProfileCard

---

# 12. Timeline Components

Single reusable timeline component.

Variants

- Project Timeline
- Activity Timeline
- Government Timeline
- Customer Timeline

---

# 13. Workflow Components

Reusable workflow visualization.

Includes

- WorkflowStepper
- WorkflowStage
- StageIndicator
- StageTimeline
- StageProgress

---

# 14. Dialog Components

- BaseDialog
- ConfirmationDialog
- DeleteDialog
- UploadDialog
- AIResponseDialog
- ProjectDialog
- TaskDialog
- UserDialog

---

# 15. Drawer Components

- BaseDrawer
- AIDrawer
- PreviewDrawer
- NotificationDrawer
- DetailsDrawer
- QuickEditDrawer

---

# 16. Customer Portal Components

- StatusSearchForm
- ProjectStatusCard
- ProgressTimeline
- CustomerUpdateCard
- PendingActionCard

---

# 17. Chart Components

Reusable wrappers around the chart library.

- BarChart
- LineChart
- DonutChart
- AreaChart
- TrendCard

---

# Component Relationships

```
Page

↓

Layout

↓

PageHeader

↓

Toolbar

↓

Business Components

↓

Common Components
```

Example

```
Project Workspace

↓

ProjectHeader

↓

WorkflowStepper

↓

ProjectSummary

↓

SmartTable

↓

StatusBadge

↓

Button
```

---

# Component Communication

Preferred communication

```
Props

↓

Events

↓

Pinia Store (shared state)

↓

Service Layer
```

Avoid

- Deep prop drilling
- Global event bus
- Direct component-to-component coupling

---

# Component Rules

Every component should:

- Have a single responsibility
- Be independently testable
- Be reusable
- Avoid business logic
- Accept configurable props
- Emit meaningful events
- Support loading state
- Support empty state where applicable

---

# Definition of Done

A reusable component is considered complete when it:

- Has a clear responsibility.
- Is configurable through props.
- Emits events instead of directly changing parent state.
- Uses TypeScript typings.
- Is responsive.
- Works in both light and dark themes.
- Has loading, empty and error states where appropriate.
- Can be reused without modification in multiple pages.

Pages must be assembled from this catalog rather than creating one-off UI elements.
````
