<script setup>
// 金价监控页:最新价 + ECharts 折线 + 配置面板
import { computed, onMounted, ref, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

import { apiGoldLatest, apiGoldHistory, apiGoldConfig, apiUpdateGoldConfig, apiGoldRefresh } from '@/api/gold'
import { useAuthStore } from '@/store/auth'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, DataZoomComponent])

const auth = useAuthStore()

const latest = ref(null)
const range = ref('24h')
const history = ref([])
const cfg = ref({ product_code: 'Au99.99', poll_interval_sec: 300, enabled: 1 })
const loading = ref(false)

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['金价(元/克)'] },
  grid: { left: 50, right: 20, top: 40, bottom: 60 },
  xAxis: {
    type: 'category',
    data: history.value.map(p => p.fetched_at),
    boundaryGap: false,
    axisLabel: { rotate: 0, formatter: (v) => v.slice(5, 16) }
  },
  yAxis: { type: 'value', scale: true, axisLabel: { formatter: '{value}' } },
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20 }],
  series: [{
    name: '金价(元/克)',
    type: 'line',
    showSymbol: false,
    smooth: true,
    data: history.value.map(p => p.price),
    areaStyle: { opacity: 0.15 },
    lineStyle: { width: 2 }
  }]
}))

async function loadAll() {
  loading.value = true
  try {
    const [a, b, c] = await Promise.all([
      apiGoldLatest(),
      apiGoldHistory(range.value),
      apiGoldConfig()
    ])
    latest.value = a.data
    history.value = b.data.items
    if (c.data) cfg.value = c.data
  } finally {
    loading.value = false
  }
}

async function onRangeChange() { await loadAll() }

async function onSaveConfig() {
  await apiUpdateGoldConfig({
    product_code: cfg.value.product_code,
    poll_interval_sec: Number(cfg.value.poll_interval_sec),
    enabled: !!cfg.value.enabled
  })
  ElMessage.success('已保存,监控进程将在 1 分钟内生效')
}

async function onRefresh() {
  const res = await apiGoldRefresh()
  ElMessage.success(`已拉取: ${res.data.price} 元/克`)
  loadAll()
}

onMounted(loadAll)
</script>

<template>
  <div v-loading="loading">
    <!-- 顶部数据卡片 -->
    <el-row :gutter="12" style="margin-bottom:12px;">
      <el-col :xs="24" :md="8">
        <el-card>
          <div style="color:#909399;font-size:13px;">最新价格 ({{ latest?.product_code || cfg.product_code }})</div>
          <div style="font-size:36px;font-weight:700;color:#e6a23c;margin:8px 0;">
            {{ latest ? latest.price.toFixed(2) : '--' }}
            <span style="font-size:14px;color:#909399;font-weight:400;">元/克</span>
          </div>
          <div style="color:#909399;font-size:12px;">{{ latest?.fetched_at || '尚无数据' }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="16">
        <el-card>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
            <div style="font-weight:600;">价格走势</div>
            <el-radio-group v-model="range" @change="onRangeChange" size="small">
              <el-radio-button value="1h">1 小时</el-radio-button>
              <el-radio-button value="24h">24 小时</el-radio-button>
              <el-radio-button value="7d">7 天</el-radio-button>
              <el-radio-button value="30d">30 天</el-radio-button>
              <el-radio-button value="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <div style="height:320px;">
            <v-chart :option="option" autoresize v-if="history.length" />
            <el-empty v-else description="该时间段内暂无数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 配置面板 -->
    <el-card>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div style="font-weight:600;">监控配置</div>
        <div>
          <el-button v-if="auth.isLoggedIn" @click="onRefresh">
            <el-icon><Refresh /></el-icon>立即拉取
          </el-button>
        </div>
      </div>
      <el-form :model="cfg" label-width="120px" :inline="false">
        <el-form-item label="品类代码">
          <el-input v-model="cfg.product_code" :disabled="!auth.isLoggedIn" style="width:240px;" />
          <span style="color:#909399;font-size:12px;margin-left:8px;">默认 Au99.99</span>
        </el-form-item>
        <el-form-item label="拉取间隔(秒)">
          <el-input-number v-model="cfg.poll_interval_sec" :min="30" :max="86400" :step="30"
                           :disabled="!auth.isLoggedIn" style="width:200px;" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="cfg.enabled" :active-value="1" :inactive-value="0" :disabled="!auth.isLoggedIn" />
        </el-form-item>
        <el-form-item v-if="auth.isLoggedIn">
          <el-button type="primary" @click="onSaveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
