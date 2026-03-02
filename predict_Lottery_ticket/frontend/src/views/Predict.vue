<template>
  <div class="predict-page">
    <!-- 页面标题 -->
    <div class="page-header animate-fade-in">
      <h1>
        <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        彩票预测
      </h1>
      <p>基于历史数据的统计分析，生成预测号码</p>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel mac-card animate-fade-in" style="animation-delay: 0.1s">
      <div class="control-row">
        <div class="control-item">
          <label>选择彩种</label>
          <el-select v-model="selectedType" placeholder="请选择彩种" @change="onTypeChange" size="large">
            <el-option label="双色球" value="ssq">
              <span>双色球</span>
              <span class="option-badge">6+1</span>
            </el-option>
            <el-option label="超级大乐透" value="dlt">
              <span>超级大乐透</span>
              <span class="option-badge">5+2</span>
            </el-option>
          </el-select>
        </div>

        <div class="control-item">
          <label>预测注数</label>
          <div class="slider-container">
            <el-slider v-model="count" :min="1" :max="10" :show-tooltip="true" />
            <span class="slider-value">{{ count }} 注</span>
          </div>
        </div>
      </div>

      <div class="method-selector">
        <label>预测方法</label>
        <div class="method-options">
          <div
            v-for="m in methods"
            :key="m.value"
            class="method-option"
            :class="{ active: method === m.value }"
            @click="method = m.value"
          >
            <div class="method-icon" v-html="m.icon"></div>
            <div class="method-info">
              <span class="method-name">{{ m.label }}</span>
              <span class="method-desc">{{ m.desc }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="action-row">
        <button class="mac-btn primary large" @click="generatePrediction" :disabled="loading">
          <svg v-if="!loading" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '生成中...' : '生成预测' }}
        </button>
      </div>
    </div>

    <!-- 预测结果 -->
    <div class="predictions animate-fade-in" style="animation-delay: 0.2s" v-if="predictions.length > 0">
      <div class="result-header">
        <h2>
          <svg viewBox="0 0 24 24" width="24" height="24" fill="#34C759">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          预测结果
        </h2>
        <el-tag type="success" size="large" effect="dark">
          预测期号: 第 {{ predictions[0]?.target_issue || '-' }} 期
        </el-tag>
      </div>

      <div class="prediction-list">
        <div
          v-for="(pred, index) in predictions"
          :key="index"
          class="prediction-card mac-card"
        >
          <div class="prediction-header">
            <span class="prediction-index">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
              第 {{ index + 1 }} 注
            </span>
            <el-tag size="small">{{ methodText }}</el-tag>
          </div>
          <div class="prediction-balls">
            <div class="ball-group">
              <span class="group-label">{{ selectedType === 'dlt' ? '前区' : '红球' }}:</span>
              <div class="balls">
                <span v-for="ball in pred.red_balls" :key="'r'+ball" class="ball red">
                  {{ ball }}
                </span>
              </div>
            </div>
            <div class="ball-group">
              <span class="group-label">{{ selectedType === 'dlt' ? '后区' : '蓝球' }}:</span>
              <div class="balls">
                <span v-for="ball in pred.blue_balls" :key="'b'+ball" class="ball blue">
                  {{ ball }}
                </span>
              </div>
            </div>
          </div>
          <div class="prediction-actions">
            <button class="mac-btn small primary" @click="saveSinglePrediction(pred, index)">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
              </svg>
              保存此注
            </button>
            <button class="mac-btn small secondary" @click="removePrediction(index)">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>

      <div class="action-buttons" v-if="predictions.length > 0">
        <button class="mac-btn success large" @click="saveAllPredictions" :disabled="saving">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          保存所有预测
        </button>
        <button class="mac-btn secondary large" @click="goToVerify">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
          </svg>
          查看已保存的预测
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state animate-fade-in" style="animation-delay: 0.2s" v-else-if="!loading">
      <svg viewBox="0 0 24 24" width="64" height="64" fill="rgba(255,255,255,0.3)">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
      </svg>
      <p>请选择彩种并生成预测</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { predict, savePredictions, getLatest } from '../api'
import { ElMessage, ElLoading } from 'element-plus'

const route = useRoute()
const router = useRouter()

const selectedType = ref('ssq')
const method = ref('smart')
const count = ref(1)
const loading = ref(false)
const saving = ref(false)
const predictions = ref([])

const methods = [
  {
    value: 'smart',
    label: '智能综合策略',
    desc: '综合多维度分析，自动生成最优预测',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" fill="#007AFF"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>'
  },
  {
    value: 'frequency',
    label: '频率分析',
    desc: '基于号码历史出现频率',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" fill="#34C759"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>'
  },
  {
    value: 'hot_cold',
    label: '冷热号',
    desc: '分析热号和冷号趋势',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" fill="#FF9500"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/></svg>'
  },
  {
    value: 'missing',
    label: '遗漏值',
    desc: '基于号码遗漏期数分析',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" fill="#AF52DE"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>'
  }
]

const methodText = computed(() => {
  const map = {
    smart: '智能综合策略',
    frequency: '频率分析',
    hot_cold: '冷热号',
    missing: '遗漏值'
  }
  return map[method.value] || method.value
})

const onTypeChange = () => {
  predictions.value = []
}

const generatePrediction = async () => {
  if (!selectedType.value) {
    ElMessage.warning('请先选择彩种')
    return
  }

  loading.value = true
  predictions.value = []

  try {
    let nextIssue = ''
    try {
      const latestRes = await getLatest(selectedType.value)
      if (latestRes.data) {
        const currentIssue = latestRes.data.issue
        const num = parseInt(currentIssue) + 1
        nextIssue = num.toString()
      }
    } catch (e) {
      console.warn('获取最新期号失败，使用默认')
    }

    const res = await predict(selectedType.value, method.value, count.value)
    predictions.value = res.data.predictions.map(pred => ({
      ...pred,
      target_issue: nextIssue
    }))
    ElMessage.success('预测生成成功')
  } catch (error) {
    ElMessage.error('预测生成失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const saveSinglePrediction = async (pred, index) => {
  if (!predictions.value.length) return

  saving.value = true
  try {
    const predictionData = [{
      lottery_type: selectedType.value,
      target_issue: pred.target_issue,
      red_balls: pred.red_balls.join(','),
      blue_balls: pred.blue_balls.join(','),
      method: method.value
    }]
    await savePredictions(selectedType.value, predictionData)
    ElMessage.success(`第 ${index + 1} 注已保存`)
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const saveAllPredictions = async () => {
  if (!predictions.value.length) {
    ElMessage.warning('没有可保存的预测')
    return
  }

  saving.value = true
  try {
    const predictionsData = predictions.value.map(pred => ({
      lottery_type: selectedType.value,
      target_issue: pred.target_issue,
      red_balls: pred.red_balls.join(','),
      blue_balls: pred.blue_balls.join(','),
      method: method.value
    }))
    const res = await savePredictions(selectedType.value, predictionsData)
    ElMessage.success(res.data.message || '预测已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const removePrediction = (index) => {
  predictions.value.splice(index, 1)
  ElMessage.info('已删除')
}

const goToVerify = () => {
  router.push({ path: '/verify', query: { type: selectedType.value } })
}

onMounted(() => {
  if (route.query.type) {
    selectedType.value = route.query.type
  }
})
</script>

<style scoped>
.predict-page {
  color: white;
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 10px;
}

.page-header p {
  opacity: 0.8;
  font-size: 16px;
}

/* 控制面板 */
.control-panel {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 28px;
  color: #333;
  margin-bottom: 32px;
}

.control-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.control-item {
  flex: 1;
}

.control-item label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.control-item :deep(.el-select) {
  width: 100%;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slider-container :deep(.el-slider) {
  flex: 1;
}

.slider-value {
  font-size: 14px;
  font-weight: 600;
  color: #007AFF;
  min-width: 50px;
}

/* 方法选择 */
.method-selector {
  margin-bottom: 24px;
}

.method-selector > label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
}

.method-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.method-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 10px;
  background: #f5f5f7;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.method-option:hover {
  background: #e8e8ed;
}

.method-option.active {
  background: rgba(0, 122, 255, 0.1);
  border-color: #007AFF;
}

.method-icon {
  flex-shrink: 0;
}

.method-info {
  display: flex;
  flex-direction: column;
}

.method-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.method-desc {
  font-size: 12px;
  color: #888;
}

/* 操作按钮 */
.action-row {
  display: flex;
  justify-content: center;
}

/* macOS 按钮 */
.mac-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.mac-btn.large {
  padding: 14px 32px;
  font-size: 16px;
}

.mac-btn.small {
  padding: 8px 14px;
  font-size: 13px;
}

.mac-btn.primary {
  background: linear-gradient(135deg, #007AFF 0%, #0056CC 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.4);
}

.mac-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 122, 255, 0.5);
}

.mac-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.mac-btn.secondary {
  background: rgba(0, 0, 0, 0.06);
  color: #333;
}

.mac-btn.secondary:hover {
  background: rgba(0, 0, 0, 0.1);
}

.mac-btn.success {
  background: linear-gradient(135deg, #34C759 0%, #228B22 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(52, 199, 89, 0.4);
}

.mac-btn.success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(52, 199, 89, 0.5);
}

/* 加载动画 */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 预测结果 */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.result-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 600;
}

.prediction-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.prediction-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 14px;
  padding: 20px;
  color: #333;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.prediction-index {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #007AFF;
}

.prediction-balls {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.ball-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-label {
  font-size: 13px;
  color: #666;
  min-width: 45px;
}

.balls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ball {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.ball.red {
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  color: white;
  box-shadow: 0 2px 8px rgba(238, 90, 90, 0.4);
}

.ball.blue {
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  color: white;
  box-shadow: 0 2px 8px rgba(9, 132, 227, 0.4);
}

.prediction-actions {
  display: flex;
  gap: 10px;
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  opacity: 0.7;
}

.empty-state svg {
  margin-bottom: 20px;
}

.empty-state p {
  font-size: 16px;
}

/* 选项徽章 */
.option-badge {
  background: linear-gradient(135deg, #007AFF, #5856D6);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  margin-left: 8px;
}

/* 动画 */
.animate-fade-in {
  animation: macFadeIn 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  opacity: 0;
}

@keyframes macFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
