/**
 * Vue Router configuration
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/repositories',
    name: 'repositories',
    component: () => import('@/views/RepositoriesView.vue'),
    meta: { title: 'Repositories' },
  },
  {
    path: '/workflows',
    name: 'workflows',
    component: () => import('@/views/WorkflowsView.vue'),
    meta: { title: 'Workflows' },
  },
  {
    path: '/workflows/:id',
    name: 'workflow-detail',
    component: () => import('@/views/WorkflowDetailView.vue'),
    props: true,
    meta: { title: 'Workflow Details' },
  },
  {
    path: '/runs/:id',
    name: 'run-detail',
    component: () => import('@/views/RunDetailView.vue'),
    props: true,
    meta: { title: 'Run Details' },
  },
  {
    path: '/jobs/:id',
    name: 'job-detail',
    component: () => import('@/views/JobDetailView.vue'),
    props: true,
    meta: { title: 'Job Details' },
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue'),
    meta: { title: 'Search' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: 'Not Found' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Update document title on route change
router.beforeEach((to, _from, next) => {
  const baseTitle = 'GitHub Actions Dashboard'
  document.title = to.meta.title ? `${to.meta.title} | ${baseTitle}` : baseTitle
  next()
})

export default router
