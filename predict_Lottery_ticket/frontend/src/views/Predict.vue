<template>
  <div class="predict-page">
    <div class="predict-header">
      <h1>彩票预测</h1>
      <p>基于历史数据的统计分析，生成预测号码</p>
    </div>

    <div class="predict-controls">
      <el-card class="control-card">
        <el-form label-width="80px">
          <el-form-item label="选择彩种">
            <el-select v-model="selectedType" placeholder="请选择彩种" @change="onTypeChange">
              <el-option label="双色球" value="ssq" />
              <el-option label="超级大乐透" value="dlt" />
            </el-select>
          </el-form-item>

          <el-form-item label="预测方法">
            <el-radio-group v-model="method">
              <el-radio label="frequency">频率分析</el-radio>
              <el-radio label="hot_cold">冷热号</el-radio>
              <el-radio label="missing">遗漏值</el-radio>
              <el-radio label="random">随机</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="预测注数">
            <el-slider v-model="count" :min="1" :max="10" show-input />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="generatePrediction" :loading="loading">
              生成预测
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="predictions" v-if="predictions.length > 0">
      <h2>预测结果</h2>
      <div class="issue-info">
        <el-tag type="success" size="large">
          预测期号: 第 {{ predictions[0]?.target_issue || '-' }} 期
        </el-tag>
      </div>
      <div class="prediction-list">
        <div
          v-for="(pred, index) in predictions"
          :key="index"
          class="prediction-card"
        >
          <div class="prediction-header">
            <span class="prediction-index">第 {{ index + 1 }} 注</span>
            <el-tag size="small">{{ methodText }}</el-tag>
          </div>
          <div class="prediction-balls">
            <div class="ball-group">
              <span class="group-label">红球:</span>
              <div class="balls">
                <span v-for="ball in pred.red_balls" :key="'r'+ball" class="ball red">
                  {{ ball }}
                </span>
              </div>
            </div>
            <div class="ball-group">
              <span class="group-label">{{ selectedType === 'dlt' ? '前区' : '蓝球' }}:</span>
              <div class="balls">
                <span v-for="ball in pred.blue_balls" :key="'b'+ball" class="ball blue">
                  {{ ball }}
                </span>
              </div>
            </div>
          </div>
          <div class="prediction-actions">
            <el-button type="primary" size="small" @click="saveSinglePrediction(pred, index)">
              保存此注
            </el-button>
            <el-button size="small" @click="removePrediction(index)">
              删除
            </el-button>
          </div>
        </div>
      </div>

      <div class="action-buttons" v-if="predictions.length > 0">
        <el-button type="success" size="large" @click="saveAllPredictions" :loading="saving">
          <el-icon><Check /></el-icon>
          保存所有预测
        </el-button>
        <el-button type="warning" size="large" @click="goToVerify">
          <el-icon><Search /></el-icon>
          查看已保存的预测
        </el-button>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="请选择彩种并生成预测" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { predict, savePredictions, getLatest } from '../api'
import { ElMessage } from 'element-plus'
import { Check, Search } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const selectedType = ref('ssq')
const method = ref('frequency')
const count = ref(1)
const loading = ref(false)
const saving = ref(false)
const predictions = ref([])

const methodText = computed(() => {
  const map = {
    frequency: '频率分析',
    hot_cold: '冷热号',
    missing: '遗漏值',
    random: '随机'
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
    // 获取最新一期期号，用于预测下一期
    let nextIssue = ''
    try {
      const latestRes = await getLatest(selectedType.value)
      if (latestRes.data) {
        // 从当前期号计算下一期
        const currentIssue = latestRes.data.issue
        const num = parseInt(currentIssue) + 1
        nextIssue = num.toString()
      }
    } catch (e) {
      console.warn('获取最新期号失败，使用默认')
    }

    const res = await predict(selectedType.value, method.value, count.value)
    // 为每个预测添加目标期号
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

.predict-header {
  text-align: center;
  margin-bottom: 30px;
}

.predict-header h1 {
  font-size: 36px;
  margin-bottom: 10px;
}

.predict-header p {
  opacity: 0.85;
}

.predict-controls {
  margin-bottom: 30px;
}

.control-card {
  max-width: 600px;
  margin: 0 auto;
  border-radius: 16px;
}

.predictions h2 {
  text-align: center;
  margin-bottom: 10px;
}

.issue-info {
  text-align: center;
  margin-bottom: 20px;
}

.prediction-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.prediction-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 20px;
  color: #333;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.prediction-index {
  font-weight: 600;
  color: #667eea;
}

.prediction-balls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ball-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-label {
  font-size: 14px;
  color: #666;
  min-width: 50px;
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
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
  padding: 20px;
}

:deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

:deep(.el-select) {
  width: 200px;
}
</style>
