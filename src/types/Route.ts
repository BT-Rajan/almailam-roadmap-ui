import type { ROUTE_NAMES } from '@/constants/routeNames'

export type RouteNameValue = (typeof ROUTE_NAMES)[keyof typeof ROUTE_NAMES]

export type LayoutName = 'auth' | 'dashboard' | 'customer-portal'

export interface BreadcrumbItem {
  label: string
  routeName?: RouteNameValue
}

declare module 'vue-router' {
  interface RouteMeta {
    layout: LayoutName
    requiresAuth?: boolean
    breadcrumbs?: BreadcrumbItem[]
  }
}
