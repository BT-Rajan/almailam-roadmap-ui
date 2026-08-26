export interface TypeActivityItem {
  id: string
  name: string
  cost: number
}

export interface TypeActivityCategory {
  id: string
  name: string
  activities: TypeActivityItem[]
}

// One checked activity from TypeActivityPickerDialog, kept flat (not
// nested under its category) for the same reason as SelectedServiceActivity
// in ServiceCatalog.ts -- consumers want to iterate picks, not re-walk a
// tree. isCoveredByService only ever comes back from the server (set once
// at project creation, see the backend's ProjectSelectedTypeActivity) --
// the wizard itself doesn't know or need to know coverage before submit.
export interface SelectedTypeActivity {
  categoryId: string
  categoryName: string
  activityId: string
  activityName: string
  cost: number
}
