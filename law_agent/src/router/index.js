import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/Home/Index.vue'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../pages/Chat/ChatWindow.vue'),
      meta: { requiresAuth: true },
    },
    // {
    //   path: '/about',
    //   name: 'about',
    //   component: () => import('../pages/About/About.vue'), // 已无此文件，如需关于页请新建或指向其他组件
    // },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/Login/Login.vue'),
    },
    {
        path: '/register',
        name: 'register',
        component: () => import('../pages/Register/signup.vue'),
    }
  ],
})

// 全局路由守卫：检查 localStorage 中的 authToken，若目标路由需要认证但未登录则跳转登录页
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some((r) => r.meta && r.meta.requiresAuth)
  const token = localStorage.getItem('authToken')
  if (requiresAuth && !token) {
    // 将原目标路径放到 query.redirect，登录后可跳回
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  next()
})

export default router
