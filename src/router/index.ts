import { createRouter, createWebHistory } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: ROUTE_NAMES.LOGIN,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Login' },
    },
    {
      path: '/status',
      name: ROUTE_NAMES.CUSTOMER_STATUS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Project Status Tracker' },
    },
    {
      path: '/dashboard',
      name: ROUTE_NAMES.DASHBOARD,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Executive Dashboard' },
    },
    {
      path: '/projects',
      name: ROUTE_NAMES.PROJECTS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Project Explorer' },
    },
    {
      path: '/projects/new',
      name: ROUTE_NAMES.PROJECT_NEW,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'New Project Wizard' },
    },
    {
      path: '/projects/:projectId',
      name: ROUTE_NAMES.PROJECT_WORKSPACE,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Project Workspace' },
    },
    {
      path: '/government/forms',
      name: ROUTE_NAMES.GOVERNMENT_FORMS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Government Forms Library' },
    },
    {
      path: '/government/authorities',
      name: ROUTE_NAMES.GOVERNMENT_AUTHORITIES,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Authority Directory' },
    },
    {
      path: '/government/submissions',
      name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Government Submission Workspace' },
    },
    {
      path: '/documents',
      name: ROUTE_NAMES.DOCUMENTS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Document Repository' },
    },
    {
      path: '/documents/:documentId',
      name: ROUTE_NAMES.DOCUMENT_VIEWER,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Document Viewer' },
    },
    {
      path: '/documents/:documentId/review',
      name: ROUTE_NAMES.DOCUMENT_REVIEW,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'AI Document Review' },
    },
    {
      path: '/tasks',
      name: ROUTE_NAMES.TASKS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Task Board' },
    },
    {
      path: '/tasks/my',
      name: ROUTE_NAMES.MY_TASKS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'My Tasks' },
    },
    {
      path: '/reports',
      name: ROUTE_NAMES.REPORTS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Dashboard Reports' },
    },
    {
      path: '/admin/users',
      name: ROUTE_NAMES.ADMIN_USERS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'User Management' },
    },
    {
      path: '/admin/workflows',
      name: ROUTE_NAMES.ADMIN_WORKFLOWS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Workflow Configuration' },
    },
    {
      path: '/admin/forms',
      name: ROUTE_NAMES.ADMIN_FORMS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Government Forms Management' },
    },
    {
      path: '/admin/ai',
      name: ROUTE_NAMES.ADMIN_AI,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'AI Configuration' },
    },
    {
      path: '/admin/company',
      name: ROUTE_NAMES.ADMIN_COMPANY,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Company Settings' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: ROUTE_NAMES.NOT_FOUND,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Page Not Found' },
    },
  ],
})

export default router
