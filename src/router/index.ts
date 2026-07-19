import { createRouter, createWebHistory } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

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
      component: () => import('@/pages/LoginPage.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/status',
      name: ROUTE_NAMES.CUSTOMER_STATUS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Project Status Tracker' },
      meta: { layout: 'auth' },
    },
    {
      path: '/dashboard',
      name: ROUTE_NAMES.DASHBOARD,
      component: () => import('@/pages/DashboardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard' }],
      },
    },
    {
      path: '/projects',
      name: ROUTE_NAMES.PROJECTS,
      component: () => import('@/pages/ProjectsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Projects' }],
      },
    },
    {
      path: '/projects/new',
      name: ROUTE_NAMES.PROJECT_NEW,
      component: () => import('@/pages/NewProjectWizardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'New Project' },
        ],
      },
    },
    {
      path: '/projects/:projectId',
      name: ROUTE_NAMES.PROJECT_WORKSPACE,
      component: () => import('@/pages/ProjectWorkspacePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'Project' },
        ],
      },
    },
    {
      path: '/government/forms',
      name: ROUTE_NAMES.GOVERNMENT_FORMS,
      component: () => import('@/pages/GovernmentFormsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Forms' },
        ],
      },
    },
    {
      path: '/government/authorities',
      name: ROUTE_NAMES.GOVERNMENT_AUTHORITIES,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Authority Directory' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Authorities' },
        ],
      },
    },
    {
      path: '/government/submissions',
      name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Government Submission Workspace' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Submissions' },
        ],
      },
    },
    {
      path: '/documents',
      name: ROUTE_NAMES.DOCUMENTS,
      component: () => import('@/pages/DocumentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Documents' }],
      },
    },
    {
      path: '/documents/:documentId',
      name: ROUTE_NAMES.DOCUMENT_VIEWER,
      component: () => import('@/pages/DocumentViewerPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Documents', routeName: ROUTE_NAMES.DOCUMENTS },
          { label: 'Viewer' },
        ],
      },
    },
    {
      path: '/documents/:documentId/review',
      name: ROUTE_NAMES.DOCUMENT_REVIEW,
      component: () => import('@/pages/DocumentReviewPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Documents', routeName: ROUTE_NAMES.DOCUMENTS },
          { label: 'AI Review' },
        ],
      },
    },
    {
      path: '/tasks',
      name: ROUTE_NAMES.TASKS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Task Board' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Tasks' }],
      },
    },
    {
      path: '/tasks/my',
      name: ROUTE_NAMES.MY_TASKS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'My Tasks' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Tasks', routeName: ROUTE_NAMES.TASKS },
          { label: 'My Tasks' },
        ],
      },
    },
    {
      path: '/reports',
      name: ROUTE_NAMES.REPORTS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Dashboard Reports' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Reports' }],
      },
    },
    {
      path: '/admin/users',
      name: ROUTE_NAMES.ADMIN_USERS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'User Management' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration' },
          { label: 'Users' },
        ],
      },
    },
    {
      path: '/admin/workflows',
      name: ROUTE_NAMES.ADMIN_WORKFLOWS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Workflow Configuration' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration' },
          { label: 'Workflows' },
        ],
      },
    },
    {
      path: '/admin/forms',
      name: ROUTE_NAMES.ADMIN_FORMS,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Government Forms Management' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration' },
          { label: 'Forms' },
        ],
      },
    },
    {
      path: '/admin/ai',
      name: ROUTE_NAMES.ADMIN_AI,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'AI Configuration' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration' },
          { label: 'AI' },
        ],
      },
    },
    {
      path: '/admin/company',
      name: ROUTE_NAMES.ADMIN_COMPANY,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Company Settings' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration' },
          { label: 'Company' },
        ],
      },
    },
    {
      path: '/:pathMatch(.*)*',
      name: ROUTE_NAMES.NOT_FOUND,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Page Not Found' },
      meta: { layout: 'auth' },
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: ROUTE_NAMES.LOGIN, query: { redirect: to.fullPath } }
  }

  if (to.name === ROUTE_NAMES.LOGIN && authStore.isAuthenticated) {
    return { name: ROUTE_NAMES.DASHBOARD }
  }

  return true
})

export default router
