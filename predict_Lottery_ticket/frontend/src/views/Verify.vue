<template>
  <div class="verify-page">
    <div class="verify-header">
      <h1>历史预测验证</h1>
      <p>查看预测历史，验证中奖情况</p>
    </div>

    <!-- 控制面板 -->
    <div class="verify-controls">
      <el-card class="control-card">
        <el-form inline>
          <el-form-item label="彩种">
            <el-select v-model="selectedType" @change="onTypeChange">
              <el-option label="全部彩种" value="" />
              <el-option label="双色球" value="ssq" />
              <el-option label="超级大乐透" value="dlt" />
            </el-select>
          </el-form-item>

          <el-form-item label="预测方法">
            <el-select v-model="filterMethod" placeholder="全部方法" clearable>
              <el-option label="频率分析" value="frequency" />
              <el-option label="冷热号" value="hot_cold" />
              <el-option label="遗漏值" value="missing" />
              <el-option label="随机" value="random" />
            </el-select>
          </el-form-item>

          <el-form-item label="验证范围">
            <el-select v-model="verifyLimit">
              <el-option label="最近50期" :value="50" />
              <el-option label="最近100期" :value="100" />
              <el-option label="最近200期" :value="200" />
              <el-option label="最近500期" :value="500" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="startVerify" :loading="verifying">
              <el-icon><Search /></el-icon>
              开始验证
            </el-button>
            <el-button @click="loadPredictions">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="danger" @click="clearPredictions" :loading="clearing">
              <el-icon><Delete /></el-icon>
              清空预测
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 统计概览卡片 -->
    <div class="stats-overview" v-if="predictions.length > 0">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card overview">
            <div class="stat-icon">📋</div>
            <div class="stat-info">
              <div class="stat-value">{{ filteredPredictions.length }}</div>
              <div class="stat-label">总预测注数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card overview">
            <div class="stat-icon">✅</div>
            <div class="stat-info">
              <div class="stat-value">{{ verifiedCount }}</div>
              <div class="stat-label">已验证</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card overview">
            <div class="stat-icon">🎯</div>
            <div class="stat-info">
              <div class="stat-value">{{ winningCount }}</div>
              <div class="stat-label">中奖</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card overview highlight">
            <div class="stat-icon">📈</div>
            <div class="stat-info">
              <div class="stat-value">{{ winRate }}%</div>
              <div class="stat-label">中奖率</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 预测记录列表 -->
    <div class="predictions-section" v-if="filteredPredictions.length > 0">
      <h2>我的预测记录</h2>

      <el-table :data="filteredPredictions" stripe class="predictions-table">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="target_issue" label="预测期号" width="100" />
        <el-table-column label="预测号码" min-width="200">
          <template #default="{ row }">
            <div class="ball-display">
              <span v-for="ball in formatBalls(row.red_balls)" :key="'r'+ball" class="ball red">
                {{ ball }}
              </span>
              <span class="plus">+</span>
              <span v-for="ball in formatBalls(row.blue_balls)" :key="'b'+ball" class="ball blue">
                {{ ball }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="方法" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ formatMethod(row.method) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lottery_type" label="彩种" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.lottery_type === 'ssq' ? 'danger' : 'primary'">
              {{ row.lottery_type === 'ssq' ? '双色球' : '大乐透' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="getPredictionStatus(row) === '已中奖'" type="success" size="small">
              {{ getPredictionStatus(row) }}
            </el-tag>
            <el-tag v-else-if="getPredictionStatus(row) === '未中奖'" type="info" size="small">
              {{ getPredictionStatus(row) }}
            </el-tag>
            <el-tag v-else-if="getPredictionStatus(row) === '未开奖'" type="warning" size="small">
              {{ getPredictionStatus(row) }}
            </el-tag>
            <el-tag v-else type="info" size="small">
              待验证
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="中奖等级" width="100">
          <template #default="{ row }">
            <template v-if="verificationResult">
              <el-tag
                v-for="detail in getPredictionResult(row)"
                :key="detail.prize"
                :type="getPrizeType(detail.prize)"
                size="small"
                style="margin-right: 4px"
              >
                {{ detail.prize }}
              </el-tag>
              <span v-if="!getPredictionResult(row).length" style="color: #999">-</span>
            </template>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        <el-table-column label="开奖日期" width="120">
          <template #default="{ row }">
            <span v-if="getPredictionResult(row).length && getPredictionResult(row)[0].open_date && getPredictionResult(row)[0].open_date.trim()">
              {{ getPredictionResult(row)[0].open_date }}
            </span>
            <span v-else-if="getPredictionStatus(row) === '未开奖'" style="color: #e6a23c">
              {{ getEstimatedDrawDate(row) }}
            </span>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-else description="暂无预测记录，请先在预测页面生成并保存预测号码" />

    <!-- 验证结果统计 -->
    <div class="verification-result" v-if="verificationResult">
      <h2>验证结果统计</h2>

      <el-row :gutter="20" class="stats-cards">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-value">{{ verificationResult.total_predictions }}</div>
            <div class="stat-label">总预测注数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-value">{{ verificationResult.verified_count }}</div>
            <div class="stat-label">已验证期数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-value">{{ verificationResult.no_draw_count }}</div>
            <div class="stat-label">未开奖期数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card highlight">
            <div class="stat-value">{{ verificationResult.win_rate }}%</div>
            <div class="stat-label">总中奖率</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 中奖统计 -->
      <el-card class="prize-stats-card" v-if="verificationResult.prize_stats && verificationResult.prize_stats.length > 0">
        <h3>中奖统计</h3>
        <div class="prize-list">
          <div
            v-for="(stat, index) in verificationResult.prize_stats"
            :key="stat.prize"
            class="prize-item"
            :class="'prize-level-' + (index + 1)"
          >
            <div class="prize-name">{{ stat.prize }}</div>
            <div class="prize-count">{{ stat.count }} 次</div>
            <div class="prize-rate">中奖率: {{ stat.rate }}%</div>
          </div>
        </div>

        <div class="total-wins">
          <span>总中奖次数: <strong>{{ verificationResult.total_wins }}</strong> 次</span>
        </div>
      </el-card>

      <el-empty v-else-if="verificationResult.verified_count > 0" description="暂无中奖记录" />

      <!-- 详细中奖记录 -->
      <div class="detailed-results" v-if="verificationResult.detailed_results && verificationResult.detailed_results.length > 0">
        <h3>详细中奖记录</h3>
        <el-table :data="verificationResult.detailed_results" stripe max-height="400">
          <el-table-column label="预测号码" min-width="180">
            <template #default="{ row }">
              <div class="ball-display small">
                <span v-for="ball in formatBalls(row.pred_red || row.pred_front)" :key="'pr'+ball" class="ball red">
                  {{ ball }}
                </span>
                <span class="plus">+</span>
                <span v-for="ball in formatBalls(row.pred_blue || row.pred_back)" :key="'pb'+ball" class="ball blue">
                  {{ ball }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="target_issue" label="预测期号" width="100" />
          <el-table-column label="开奖号码" min-width="180">
            <template #default="{ row }">
              <div class="ball-display small">
                <span v-for="ball in formatBalls(row.draw_red || row.draw_front)" :key="'dr'+ball" class="ball red">
                  {{ ball }}
                </span>
                <span class="plus">+</span>
                <span v-for="ball in formatBalls(row.draw_blue || row.draw_back)" :key="'db'+ball" class="ball blue">
                  {{ ball }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="prize" label="中奖等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getPrizeType(row.prize)" size="small">{{ row.prize }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="开奖日期" width="110">
            <template #default="{ row }">
              {{ row.open_date && row.open_date.trim() ? row.open_date : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="匹配数" width="100">
            <template #default="{ row }">
              <span v-if="selectedType === 'ssq' || !selectedType">
                红球: {{ row.red_matches }} | 蓝球: {{ row.blue_matches }}
              </span>
              <span v-else>
                前区: {{ row.front_matches }} | 后区: {{ row.back_matches }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getAllPredictions, verifyPredictions, clearPredictions as clearPredictionsAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Delete } from '@element-plus/icons-vue'

const route = useRoute()

const selectedType = ref('ssq')
const filterMethod = ref('')
const verifyLimit = ref(100)
const predictions = ref([])
const verificationResult = ref(null)
const loading = ref(false)
const verifying = ref(false)
const clearing = ref(false)

// 筛选后的预测列表
const filteredPredictions = computed(() => {
  let result = predictions.value

  // 按彩种筛选
  if (selectedType.value) {
    result = result.filter(p => p.lottery_type === selectedType.value)
  }

  // 按方法筛选
  if (filterMethod.value) {
    result = result.filter(p => p.method === filterMethod.value)
  }

  return result
})

// 统计计算
const verifiedCount = computed(() => {
  if (!verificationResult.value) return 0
  return verificationResult.value.verified_count || 0
})

const winningCount = computed(() => {
  if (!verificationResult.value) return 0
  return verificationResult.value.total_wins || 0
})

const winRate = computed(() => {
  if (!verificationResult.value || !verifiedCount.value) return 0
  return verificationResult.value.win_rate || 0
})

const formatBalls = (ballsStr) => {
  if (!ballsStr) return []
  return ballsStr.split(',').map(b => b.trim())
}

const formatMethod = (method) => {
  const map = {
    frequency: '频率分析',
    hot_cold: '冷热号',
    missing: '遗漏值',
    random: '随机'
  }
  return map[method] || method
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getPrizeType = (prize) => {
  const typeMap = {
    '一等奖': 'danger',
    '二等奖': 'warning',
    '三等奖': 'warning',
    '四等奖': 'success',
    '五等奖': 'success',
    '六等奖': 'info',
    '七等奖': 'info',
    '八等奖': 'info',
    '九等奖': 'info'
  }
  return typeMap[prize] || 'info'
}

// 获取单条预测的状态
const getPredictionStatus = (pred) => {
  if (!verificationResult.value || !verificationResult.value.detailed_results) {
    return '待验证'
  }

  const result = verificationResult.value.detailed_results.find(r => r.prediction_id === pred.id)
  if (!result) {
    return '待验证'
  }

  if (result.prize === '未开奖') {
    return '未开奖'
  }

  if (result.prize_level > 0) {
    return '已中奖'
  }

  return '未中奖'
}

// 获取单条预测的中奖结果
const getPredictionResult = (pred) => {
  if (!verificationResult.value || !verificationResult.value.detailed_results) {
    return []
  }

  return verificationResult.value.detailed_results.filter(r => r.prediction_id === pred.id)
}

// 计算预计开奖日期
// 双色球: 周二、周四、周日开奖 (3次/周)
// 大乐透: 周一、周三、周六开奖 (3次/周)
const getEstimatedDrawDate = (pred) => {
  const lotteryType = pred.lottery_type

  // 双色球开奖日: 周二(2), 周四(4), 周日(0)
  // 大乐透开奖日: 周一(1), 周三(3), 周六(5)
  const drawDays = lotteryType === 'ssq' ? [2, 4, 0] : [1, 3, 5]

  // 从当前日期开始找下一个开奖日
  const today = new Date()
  const checkDate = new Date(today)

  // 最多检查 10 天
  for (let i = 0; i < 10; i++) {
    const dayOfWeek = checkDate.getDay()
    if (drawDays.includes(dayOfWeek)) {
      const year = checkDate.getFullYear()
      const month = String(checkDate.getMonth() + 1).padStart(2, '0')
      const day = String(checkDate.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
    checkDate.setDate(checkDate.getDate() + 1)
  }

  return '-'
}

const onTypeChange = () => {
  predictions.value = []
  verificationResult.value = null
  loadPredictions()
}

const loadPredictions = async () => {
  loading.value = true
  try {
    // 获取所有预测记录
    const res = await getAllPredictions()
    predictions.value = res.data.predictions || []

    if (predictions.value.length === 0) {
      ElMessage.info('暂无预测记录')
    }
  } catch (error) {
    ElMessage.error('加载预测记录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const startVerify = async () => {
  if (filteredPredictions.value.length === 0) {
    ElMessage.warning('没有可验证的预测')
    return
  }

  // 获取当前筛选的彩种
  const type = selectedType.value || 'ssq'

  verifying.value = true
  verificationResult.value = null

  try {
    const res = await verifyPredictions(type, verifyLimit.value)
    verificationResult.value = res.data
    ElMessage.success('验证完成')
  } catch (error) {
    ElMessage.error('验证失败: ' + error.message)
  } finally {
    verifying.value = false
  }
}

const clearPredictions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有预测记录吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    clearing.value = true

    // 清空所有彩种的预测
    await clearPredictionsAPI('ssq')
    await clearPredictionsAPI('dlt')

    predictions.value = []
    verificationResult.value = null
    ElMessage.success('预测记录已清空')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败: ' + error.message)
    }
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  if (route.query.type) {
    selectedType.value = route.query.type
  }
  loadPredictions()
})
</script>

<style scoped>
.verify-page {
  color: white;
}

.verify-header {
  text-align: center;
  margin-bottom: 30px;
}

.verify-header h1 {
  font-size: 36px;
  margin-bottom: 10px;
}

.verify-header p {
  opacity: 0.85;
}

.verify-controls {
  margin-bottom: 20px;
}

.control-card {
  max-width: 900px;
  margin: 0 auto;
  border-radius: 16px;
}

.control-card :deep(.el-form-item__label) {
  color: #333;
  font-weight: 500;
}

.control-card :deep(.el-select) {
  width: 130px;
}

.control-card :deep(.el-select .el-input__wrapper) {
  background-color: #fff;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.control-card :deep(.el-select .el-input__inner) {
  color: #333;
}

/* 统计概览 */
.stats-overview {
  margin-bottom: 20px;
}

.stats-overview .stat-card.overview {
  display: flex;
  align-items: center;
  gap: 15px;
  border-radius: 16px;
}

.stats-overview .stat-icon {
  font-size: 32px;
}

.stats-overview .stat-info {
  flex: 1;
}

.stats-overview .stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stats-overview .stat-label {
  font-size: 13px;
  color: #666;
}

.stats-overview .stat-card.highlight {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.stats-overview .stat-card.highlight .stat-value,
.stats-overview .stat-card.highlight .stat-label {
  color: white;
}

/* 预测记录 */
.predictions-section {
  margin-bottom: 30px;
}

.predictions-section h2 {
  text-align: center;
  margin-bottom: 20px;
}

.predictions-table {
  border-radius: 16px;
  overflow: hidden;
}

.ball-display {
  display: flex;
  gap: 4px;
  align-items: center;
}

.ball {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
}

.ball.red {
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  color: white;
}

.ball.blue {
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  color: white;
}

.ball-display.small .ball {
  width: 22px;
  height: 22px;
  font-size: 10px;
}

.plus {
  margin: 0 4px;
  font-weight: bold;
}

/* 验证结果 */
.verification-result {
  margin-top: 30px;
}

.verification-result h2 {
  text-align: center;
  margin-bottom: 20px;
}

.verification-result h3 {
  margin-bottom: 15px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  border-radius: 16px;
}

.stat-card.highlight {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #333;
}

.stat-card.highlight .stat-value {
  color: white;
}

.stat-label {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 5px;
}

.prize-stats-card {
  margin-bottom: 20px;
  border-radius: 16px;
}

.prize-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.prize-item {
  background: rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  text-align: center;
  border-left: 4px solid #409eff;
}

.prize-item.prize-level-1 {
  border-left-color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.prize-item.prize-level-2 {
  border-left-color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.prize-item.prize-level-3 {
  border-left-color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.prize-item.prize-level-4 {
  border-left-color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.prize-item.prize-level-5 {
  border-left-color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.prize-name {
  font-weight: 600;
  margin-bottom: 5px;
}

.prize-count {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.prize-rate {
  font-size: 12px;
  opacity: 0.85;
  margin-top: 5px;
}

.total-wins {
  text-align: center;
  padding: 15px;
  background: rgba(103, 194, 58, 0.1);
  border-radius: 8px;
  font-size: 16px;
}

.total-wins strong {
  color: #67c23a;
  font-size: 24px;
}

.detailed-results {
  margin-top: 30px;
}

.detailed-results h3 {
  margin-bottom: 15px;
}

:deep(.el-table) {
  --el-table-bg-color: rgba(255, 255, 255, 0.95);
  --el-table-text-color: #333;
}

:deep(.el-card) {
  background: rgba(255, 255, 255, 0.95);
}
</style>
