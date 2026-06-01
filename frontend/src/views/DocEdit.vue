<script setup>
// 文档新增/编辑:Markdown 编辑器 + 图片上传(对接 /api/upload)
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { apiCreateDoc, apiGetDoc, apiUpdateDoc, apiUpload, apiCategories } from '@/api/docs'

const route = useRoute()
const router = useRouter()

const isEdit = ref(false)
const submitting = ref(false)
const cats = ref([])

const form = reactive({
  title: '',
  category: '默认',
  content: ''
})

async function loadCats() {
  const res = await apiCategories()
  cats.value = res.data
}

async function load() {
  if (route.params.id) {
    isEdit.value = true
    const res = await apiGetDoc(route.params.id)
    Object.assign(form, {
      title: res.data.title,
      category: res.data.category,
      content: res.data.content
    })
  }
}

// md-editor-v3 上传钩子:files 是 File[] -> 调 /api/upload -> callback 接收 url 列表
async function onUploadImg(files, callback) {
  try {
    const urls = []
    for (const f of files) {
      const res = await apiUpload(f)
      urls.push(res.data.url)
    }
    callback(urls)
  } catch (e) {
    ElMessage.error('图片上传失败')
  }
}

async function onSave() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await apiUpdateDoc(route.params.id, form)
      ElMessage.success('已保存')
      router.push(`/docs/${route.params.id}`)
    } else {
      const res = await apiCreateDoc(form)
      ElMessage.success('已创建')
      router.push(`/docs/${res.data.id}`)
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => { load(); loadCats() })
</script>

<template>
  <div>
    <el-page-header @back="router.back()" style="margin-bottom:12px;">
      <template #content>{{ isEdit ? '编辑文档' : '新建文档' }}</template>
      <template #extra>
        <el-button type="primary" :loading="submitting" @click="onSave">
          <el-icon><Check /></el-icon>保存
        </el-button>
      </template>
    </el-page-header>

    <el-card style="margin-bottom:12px;">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="分类">
          <el-autocomplete
            v-model="form.category"
            :fetch-suggestions="(qs, cb) => cb(cats.filter(c => !qs || c.category.includes(qs)).map(c => ({ value: c.category })))"
            placeholder="可输入新分类或选择已有"
            style="width: 280px;" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <MdEditor
        v-model="form.content"
        :on-upload-img="onUploadImg"
        previewTheme="default"
        style="height: 65vh;" />
    </el-card>
  </div>
</template>
