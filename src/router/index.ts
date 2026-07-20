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
      path: '/customer-portal',
      name: 'customer-portal',
      component: () => import('@/pages/CustomerPortalLoginPage.vue'),
      meta: { layout: 'customer-portal' },
    },
    {
      path: '/customer-portal/:projectId',
      name: 'customer-project',
      component: () => import('@/pages/CustomerProjectViewPage.vue'),
      meta: { layout: 'customer-portal' },
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
      path: '/clients',
      name: ROUTE_NAMES.CLIENTS,
      component: () => import('@/pages/ClientsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Clients' }],
      },
    },
    {
      path: '/clients/new',
      name: ROUTE_NAMES.CLIENT_NEW,
      component: () => import('@/pages/NewClientWizardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'New Client' },
        ],
      },
    },
    {
      path: '/clients/:clientId',
      name: ROUTE_NAMES.CLIENT_WORKSPACE,
      component: () => import('@/pages/ClientWorkspacePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'Client' },
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
      component: () => import('@/pages/GovernmentSubmissionsPage.vue'),
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
      component: () => import('@/pages/TasksPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Tasks' }],
      },
    },
    {
      path: '/tasks/my',
      name: ROUTE_NAMES.MY_TASKS,
      component: () => import('@/pages/MyTasksPage.vue'),
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
      component: () => import('@/pages/ReportsListPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Reports' }],
      },
    },
    {
      path: '/reports/executive',
      name: ROUTE_NAMES.REPORT_EXECUTIVE,
      component: () => import('@/pages/ExecutiveReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Executive Summary' },
        ],
      },
    },
    {
      path: '/reports/project',
      name: ROUTE_NAMES.REPORT_PROJECT,
      component: () => import('@/pages/ProjectReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Project Performance' },
        ],
      },
    },
    {
      path: '/reports/workload',
      name: ROUTE_NAMES.REPORT_WORKLOAD,
      component: () => import('@/pages/WorkloadReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Team Workload' },
        ],
      },
    },
    {
      path: '/admin',
      name: ROUTE_NAMES.ADMIN,
      component: () => import('@/pages/AdministrationPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Administration' }],
      },
    },
    {
      path: '/admin/users',
      name: ROUTE_NAMES.ADMIN_USERS,
      component: () => import('@/pages/UserManagementPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Users' },
        ],
      },
    },
    {
      path: '/admin/workflows',
      name: ROUTE_NAMES.ADMIN_WORKFLOWS,
      component: () => import('@/pages/AdminWorkflowsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Workflows' },
        ],
      },
    },
    {
      path: '/admin/forms',
      name: ROUTE_NAMES.ADMIN_FORMS,
      component: () => import('@/pages/AdminFormsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Forms' },
        ],
      },
    },
    {
      path: '/admin/ai',
      name: ROUTE_NAMES.ADMIN_AI,
      component: () => import('@/pages/AdminAIPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'AI' },
        ],
      },
    },
    {
      path: '/admin/company',
      name: ROUTE_NAMES.ADMIN_COMPANY,
      component: () => import('@/pages/AdminCompanyPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Company' },
        ],
      },
    },
    {
      path: '/messages',
      name: ROUTE_NAMES.MESSAGE_CENTRE,
      component: () => import('@/pages/MessageCentrePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Message Centre' }],
      },
    },
    {
      path: '/payments',
      name: ROUTE_NAMES.PAYMENTS,
      component: () => import('@/pages/PaymentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Payments' }],
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
