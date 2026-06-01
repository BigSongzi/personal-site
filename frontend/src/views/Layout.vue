<script setup>
// 全站布局:顶部导航 + 主内容区
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/docs')) return '/docs'
  if (route.path.startsWith('/gold')) return '/gold'
  return route.path
})

function logout() {
  auth.clear()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <el-container style="height:100%;">
    <el-header style="background:#fff;border-bottom:1px solid #ebeef5;display:flex;align-items:center;padding:0 16px;">
      <div style="font-weight:700;font-size:18px;margin-right:32px;">个人站</div>
      <el-menu mode="horizontal" :default-active="activeMenu" :ellipsis="false" router style="flex:1;border:0;">
        <el-menu-item index="/docs">
          <el-icon><Document /></el-icon>知识文档
        </el-menu-item>
        <el-menu-item index="/gold">
          <el-icon><TrendCharts /></el-icon>金价监控
        </el-menu-item>
      </el-menu>
      <div>
        <template v-if="auth.isLoggedIn">
          <el-tag type="success" size="small" style="margin-right:8px;" class="hide-on-mobile">
            {{ auth.username }}
          </el-tag>
          <el-button size="small" @click="logout">退出</el-button>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="router.push('/login')">登录</el-button>
        </template>
      </div>
    </el-header>
    <el-main style="padding:0;">
      <div class="page-container">
        <router-view />
      </div>
    </el-main>
  </el-container>
</template>
