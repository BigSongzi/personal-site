// 路由表:Layout 嵌套子路由
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/docs',
    children: [
      { path: 'docs', name: 'DocList', component: () => import('@/views/DocList.vue'), meta: { public: true } },
      { path: 'docs/new', name: 'DocNew', component: () => import('@/views/DocEdit.vue'), meta: { requiresAuth: true } },
      { path: 'docs/:id', name: 'DocView', component: () => import('@/views/DocView.vue'), meta: { public: true } },
      { path: 'docs/:id/edit', name: 'DocEdit', component: () => import('@/views/DocEdit.vue'), meta: { requiresAuth: true } },
      { path: 'gold', name: 'Gold', component: () => import('@/views/Gold.vue'), meta: { public: true } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/docs' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫:仅 requiresAuth 路由强制登录,public 与一般路由公开
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
