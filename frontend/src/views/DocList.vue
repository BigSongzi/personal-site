<script setup>
// 文档列表 + 搜索 + 分类过滤 + 分页
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiListDocs, apiCategories, apiDeleteDoc } from '@/api/docs'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const query = reactive({ keyword: '', category: '', page: 1, page_size: 12 })
const total = ref(0)
const list = ref([])
const cats = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await apiListDocs(query)
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const res = await apiCategories()
  cats.value = res.data
}

function onSearch() {
  query.page = 1
  load()
}

function gotoView(id) { router.push(`/docs/${id}`) }
function gotoEdit(id) { router.push(`/docs/${id}/edit`) }
function gotoNew()   { router.push('/docs/new') }

async function onDelete(item) {
  await ElMessageBox.confirm(`确认删除文档《${item.title}》?`, '确认', { type: 'warning' })
  await apiDeleteDoc(item.id)
  ElMessage.success('已删除')
  load()
  loadCategories()
}

onMounted(() => { load(); loadCategories() })
watch(() => query.page, load)
</script>

<template>
  <div>
    <!-- 工具条 -->
    <el-card style="margin-bottom:12px;">
      <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
        <el-input v-model="query.keyword" placeholder="搜索标题/内容/分类" clearable
                  style="width:280px;" @keyup.enter="onSearch" @clear="onSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="query.category" placeholder="全部分类" clearable
                   style="width:180px;" @change="onSearch" @clear="onSearch">
          <el-option v-for="c in cats" :key="c.category" :label="`${c.category} (${c.n})`" :value="c.category" />
        </el-select>
        <el-button type="primary" @click="onSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <span style="flex:1;"></span>
        <el-button v-if="auth.isLoggedIn" type="success" @click="gotoNew">
          <el-icon><Plus /></el-icon>新建文档
        </el-button>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-row v-loading="loading" :gutter="12">
      <el-col v-for="item in list" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6" style="margin-bottom:12px;">
        <el-card class="doc-card" shadow="hover" @click="gotoView(item.id)">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <h3 style="margin:0;font-size:16px;line-height:1.4;flex:1;">{{ item.title }}</h3>
            <el-tag size="small" effect="plain">{{ item.category }}</el-tag>
          </div>
          <p style="color:#606266;font-size:13px;margin:8px 0 0 0;
                    display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;
                    overflow:hidden;">
            {{ item.summary || '(无摘要)' }}
          </p>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
            <span style="color:#909399;font-size:12px;">{{ item.updated_at }}</span>
            <span v-if="auth.isLoggedIn" @click.stop>
              <el-button size="small" link @click="gotoEdit(item.id)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" link type="danger" @click="onDelete(item)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && list.length === 0" description="暂无文档" />

    <!-- 分页 -->
    <div style="display:flex;justify-content:center;margin-top:12px;">
      <el-pagination
        v-if="total > query.page_size"
        v-model:current-page="query.page"
        :page-size="query.page_size"
        :total="total"
        layout="prev, pager, next, total"
        background />
    </div>
  </div>
</template>
