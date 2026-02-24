<template>
  <div class="analysis-page">
    <div class="analysis-header">
      <h1>数据分析</h1>
      <p>查看历史数据统计，了解号码走势</p>
    </div>

    <div class="analysis-controls">
      <el-select v-model="selectedType" placeholder="选择彩种" @change="loadData">
        <el-option label="双色球" value="ssq" />
        <el-option label="超级大乐透" value="dlt" />
      </el-select>
    </div>

    <div class="stats-overview" v-if="statistics">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">📊</div>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.total_records }}</div>
                <div class="stat-label">历史期数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">🔥</div>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.red_hot?.slice(0, 5).join(', ') }}</div>
                <div class="stat-label">红球热号 Top5</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">❄️</div>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.red_cold?.slice(0, 5).join(', ') }}</div>
                <div class="stat-label">红球冷号 Top5</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="charts-section" v-if="statistics">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球出现频率</h3>
            <div ref="redChart" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>蓝球出现频率</h3>
            <div ref="blueChart" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球奇偶比分布</h3>
            <div ref="oddEvenChart" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球区间分布</h3>
            <div ref="rangeChart" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 新增图表 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球遗漏值分布</h3>
            <div ref="missingChart" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球尾数分布</h3>
            <div ref="tailChart" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球和值分布</h3>
            <div ref="sumChart" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>红球连号统计</h3>
            <div ref="consecutiveChart" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="history-section" v-if="history.length > 0">
      <h3>历史开奖数据</h3>
      <el-table :data="history" stripe style="width: 100%">
        <el-table-column prop="issue" label="期号" width="120" />
        <el-table-column label="红球">
          <template #default="{ row }">
            <span class="table-red">{{ row.red_balls }}</span>
          </template>
        </el-table-column>
        <el-table-column label="蓝球">
          <template #default="{ row }">
            <span class="table-blue">{{ row.blue_ball }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="open_date" label="开奖日期" />
      </el-table>
    </div>

    <el-empty v-else description="暂无数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getStatistics, getHistory } from '../api'

const selectedType = ref('ssq')
const statistics = ref(null)
const history = ref([])
const redChart = ref(null)
const blueChart = ref(null)
const oddEvenChart = ref(null)
const rangeChart = ref(null)
const missingChart = ref(null)
const tailChart = ref(null)
const sumChart = ref(null)
const consecutiveChart = ref(null)

const loadData = async () => {
  try {
    const [statsRes, historyRes] = await Promise.all([
      getStatistics(selectedType.value),
      getHistory(selectedType.value, 50)
    ])

    statistics.value = statsRes.data
    history.value = historyRes.data.data

    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const renderCharts = () => {
  if (!statistics.value) return

  // 红球频率图
  if (redChart.value) {
    const redData = Object.entries(statistics.value.red_frequency || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)

    echarts.init(redChart.value).setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: redData.map(d => d[0]) },
      yAxis: { type: 'value' },
      series: [{
        data: redData.map(d => d[1]),
        type: 'bar',
        itemStyle: { color: '#e74c3c' }
      }]
    })
  }

  // 蓝球频率图
  if (blueChart.value) {
    const blueData = Object.entries(statistics.value.blue_frequency || {})
      .sort((a, b) => b[1] - a[1])

    echarts.init(blueChart.value).setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: blueData.map(d => d[0]) },
      yAxis: { type: 'value' },
      series: [{
        data: blueData.map(d => d[1]),
        type: 'bar',
        itemStyle: { color: '#3498db' }
      }]
    })
  }

  // 奇偶比分布
  if (oddEvenChart.value) {
    const oddEvenData = statistics.value.odd_even_distribution || {}
    const labels = Object.keys(oddEvenData).map(k => k.replace(/[()]/g, ''))

    echarts.init(oddEvenChart.value).setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: Object.entries(oddEvenData).map(([key, value]) => ({
          name: key.replace(/[()]/g, ''),
          value
        }))
      }]
    })
  }

  // 区间分布
  if (rangeChart.value) {
    const rangeData = statistics.value.range_distribution || {}
    const labels = selectedType.value === 'ssq'
      ? ['1-11', '12-22', '23-33']
      : ['1-12', '13-24', '25-35']

    echarts.init(rangeChart.value).setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value' },
      series: [{
        data: Object.values(rangeData),
        type: 'bar',
        itemStyle: { color: '#667eea' }
      }]
    })
  }

  // 遗漏值分布
  if (missingChart.value) {
    const missingData = statistics.value.missing_distribution || {}

    echarts.init(missingChart.value).setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(missingData) },
      yAxis: { type: 'value' },
      series: [{
        data: Object.values(missingData),
        type: 'bar',
        itemStyle: { color: '#e74c3c' }
      }]
    })
  }

  // 尾数分布
  if (tailChart.value) {
    const tailData = statistics.value.tail_distribution || {}

    echarts.init(tailChart.value).setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: Object.entries(tailData).map(([key, value]) => ({
          name: key + '尾',
          value
        }))
      }]
    })
  }

  // 和值分布
  if (sumChart.value) {
    const sumData = statistics.value.sum_distribution || {}

    echarts.init(sumChart.value).setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(sumData) },
      yAxis: { type: 'value' },
      series: [{
        data: Object.values(sumData),
        type: 'bar',
        itemStyle: { color: '#f39c12' }
      }]
    })
  }

  // 连号统计
  if (consecutiveChart.value) {
    const consecutiveData = statistics.value.consecutive_stats || {}

    const consecutiveLabels = {
      'none': '无连号',
      '2': '2连号',
      '3': '3连号',
      '2+': '2连+'
    }

    echarts.init(consecutiveChart.value).setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: Object.entries(consecutiveData).map(([key, value]) => ({
          name: consecutiveLabels[key] || key,
          value
        }))
      }]
    })
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.analysis-page {
  color: white;
}

.analysis-header {
  text-align: center;
  margin-bottom: 30px;
}

.analysis-header h1 {
  font-size: 36px;
  margin-bottom: 10px;
}

.analysis-controls {
  text-align: center;
  margin-bottom: 30px;
}

.stats-overview {
  margin-bottom: 30px;
}

.stat-card {
  border-radius: 16px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 40px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-card {
  border-radius: 16px;
  color: #333;
}

.chart-card h3 {
  margin-bottom: 15px;
  font-size: 16px;
}

.chart {
  height: 300px;
}

.history-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 20px;
  color: #333;
}

.history-section h3 {
  margin-bottom: 15px;
}

.table-red {
  color: #e74c3c;
  font-weight: 600;
}

.table-blue {
  color: #3498db;
  font-weight: 600;
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
}
</style>
