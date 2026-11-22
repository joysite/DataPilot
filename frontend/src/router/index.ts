
import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'overview',
          component: () => import('../views/OverviewView.vue'),
        },
        {
          path: 'agent',
          name: 'agent',
          component: () => import('../views/AgentChatView.vue'),
        },
        {
          path: 'data-management',
          name: 'data-management',
          component: () => import('../views/DataManagementView.vue'),
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('../views/AnalyticsView.vue'),
        },
        {
          path: 'anomalies',
          name: 'anomalies',
          component: () => import('../views/AnomaliesView.vue'),
        },
      ],
    },
  ],
})

export default router
