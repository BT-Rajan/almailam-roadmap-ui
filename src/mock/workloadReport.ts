import type { ChartDataPoint, ReportMetric } from '@/types/Report'

export interface WorkloadTeamMember {
  name: string
  role: string
  department: string
  allocation: number
  capacity: number
  projects: number
  overallocated: boolean
}

// NOTE: There is no backend model for team capacity/allocation tracking
// (no such fields exist on the User model or anywhere in schema.sql), so
// this page cannot be wired to a real endpoint the way the other report
// pages were. This data stays as clearly-scoped mock data behind a
// service, matching the app's convention for everything else, rather
// than sitting inline in the component. Building this out for real would
// need genuine capacity/allocation fields captured somewhere upstream.
export const WORKLOAD_TEAM_METRICS: ReportMetric[] = [
  {
    label: 'Total Team Members',
    value: 3,
    change: { direction: 'up', percentage: 0 },
    color: 'primary',
  },
  {
    label: 'Average Utilization',
    value: '82%',
    change: { direction: 'up', percentage: 4 },
    color: 'info',
  },
  {
    label: 'Overallocated Staff',
    value: 0,
    unit: 'persons',
    change: { direction: 'down', percentage: 0 },
    color: 'warning',
  },
  {
    label: 'Capacity Available',
    value: '18%',
    change: { direction: 'up', percentage: 6 },
    color: 'neutral',
  },
]

export const WORKLOAD_BY_DEPARTMENT: ChartDataPoint[] = [
  { label: 'Structural Engineering', value: 2, color: '#8B5CF6' },
  { label: 'MEP Engineering', value: 2, color: '#06B6D4' },
  { label: 'Fire & Safety', value: 1, color: '#F59E0B' },
]

export const WORKLOAD_DEPARTMENT_UTILIZATION: ChartDataPoint[] = [
  { label: 'Structural Engineering', value: 90, color: '#8B5CF6' },
  { label: 'MEP Engineering', value: 88, color: '#06B6D4' },
  { label: 'Fire & Safety', value: 68, color: '#F59E0B' },
]

export const WORKLOAD_TEAM_MEMBERS: WorkloadTeamMember[] = [
  {
    name: 'Layla Haddad',
    role: 'Structural Engineer',
    department: 'Structural Engineering',
    allocation: 90,
    capacity: 100,
    projects: 2,
    overallocated: false,
  },
  {
    name: 'Ahmed Rashid',
    role: 'MEP Engineer',
    department: 'MEP Engineering',
    allocation: 88,
    capacity: 100,
    projects: 2,
    overallocated: false,
  },
  {
    name: 'Mohammed Iqbal',
    role: 'Fire & Safety Engineer',
    department: 'Fire & Safety',
    allocation: 68,
    capacity: 100,
    projects: 1,
    overallocated: false,
  },
]
