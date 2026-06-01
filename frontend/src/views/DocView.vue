<script setup>
// 文档详情:只读 Markdown 预览
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import { apiGetDoc } from '@/api/docs'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const doc = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await apiGetDoc(route.params.id)
    doc.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="router.back()" style="margin-bottom:12px;">
      <template #content>
        <span style="font-weight:600;">{{ doc?.title || '加载中…' }}</span>
      </template>
      <template #extra>
        <el-button v-if="auth.isLoggedIn && doc" type="primary" size="small" @click="router.push(`/docs/${doc.id}/edit`)">
          <el-icon><Edit /></el-icon>编辑
        </el-button>
      </template>
    </el-page-header>

    <el-card v-if="doc">
      <div style="display:flex;gap:12px;align-items:center;color:#909399;font-size:13px;margin-bottom:12px;">
        <el-tag size="small">{{ doc.category }}</el-tag>
        <span>创建于 {{ doc.created_at }}</span>
        <span>·</span>
        <span>更新于 {{ doc.updated_at }}</span>
      </div>
      <MdPreview :modelValue="doc.content || ''" />
    </el-card>
  </div>
</template>
