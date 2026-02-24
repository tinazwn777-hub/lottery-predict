<template>
  <div class="home">
    <div class="hero">
      <h1>智能彩票预测系统</h1>
      <p>基于历史数据的统计分析，助您发现号码规律</p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="$router.push('/predict')">
          开始预测
        </el-button>
        <el-button size="large" @click="$router.push('/analysis')">
          查看分析
        </el-button>
      </div>
    </div>

    <div class="features">
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>数据采集</h3>
        <p>自动抓取最新开奖数据，保持数据时效性</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <h3>智能预测</h3>
        <p>多种统计方法结合，提供预测参考</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📈</div>
        <h3>数据分析</h3>
        <p>深入分析号码频率、冷热号、奇偶比</p>
      </div>
    </div>

    <div class="quick-start">
      <h2>快速开始</h2>
      <div class="lottery-cards">
        <div
          v-for="lottery in lotteries"
          :key="lottery.code"
          class="lottery-card"
          @click="goToPredict(lottery.code)"
        >
          <h3>{{ lottery.name }}</h3>
          <p class="lottery-info">
            红球: {{ lottery.red_count }}个 | 蓝球: {{ lottery.blue_count }}个
          </p>
          <div class="lottery-latest" v-if="lottery.latest">
            <div class="latest-header">
              <span class="label">第 {{ lottery.latest.issue }} 期已开奖</span>
              <span class="date">{{ lottery.latest.open_date || '未知日期' }}</span>
            </div>
            <div class="balls">
              <span class="red">{{ lottery.latest.red_balls }}</span>
              <span class="blue">{{ lottery.latest.blue_ball }}</span>
            </div>
          </div>
          <div class="lottery-latest" v-else>
            <span class="label">暂无数据，请先刷新</span>
          </div>
        </div>
      </div>
    </div>

    <div class="actions-section">
      <el-input-number v-model="crawlLimit" :min="1" :max="500" />
      <el-button type="success" @click="handleCrawl">
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLotteryTypes, getLatest, crawlData } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const lotteries = ref([])
const crawlLimit = ref(50)

const fetchData = async () => {
  try {
    const typesRes = await getLotteryTypes()
    const types = typesRes.data.types

    // 获取每个彩种的最新的开奖数据
    const lotteriesData = []
    for (const type of types) {
      try {
        const latestRes = await getLatest(type.code)
        lotteriesData.push({
          ...type,
          latest: latestRes.data
        })
      } catch {
        lotteriesData.push({
          ...type,
          latest: null
        })
      }
    }
    lotteries.value = lotteriesData
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

const goToPredict = (code) => {
  router.push({ path: '/predict', query: { type: code } })
}

const handleCrawl = async () => {
  try {
    const loading = ElMessage.loading('正在爬取数据...')
    await crawlData(crawlLimit.value)
    loading.close()
    ElMessage.success(`数据刷新成功 (${crawlLimit.value}期)`)
    fetchData()
  } catch (error) {
    ElMessage.error('数据刷新失败: ' + error.message)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.home {
  color: white;
}

.hero {
  text-align: center;
  padding: 60px 20px;
}

.hero h1 {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero p {
  font-size: 20px;
  opacity: 0.9;
  margin-bottom: 30px;
}

.hero-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 50px 0;
}

.feature-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 30px;
  text-align: center;
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.feature-card h3 {
  font-size: 20px;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 14px;
  opacity: 0.85;
}

.quick-start {
  margin-top: 50px;
}

.quick-start h2 {
  text-align: center;
  margin-bottom: 30px;
  font-size: 28px;
}

.lottery-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.lottery-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 25px;
  cursor: pointer;
  transition: all 0.3s;
  color: #333;
}

.lottery-card:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.lottery-card h3 {
  font-size: 22px;
  color: #667eea;
  margin-bottom: 10px;
}

.lottery-info {
  color: #666;
  font-size: 14px;
  margin-bottom: 15px;
}

.lottery-latest {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
}

.lottery-latest .latest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.lottery-latest .label {
  font-size: 14px;
  font-weight: 600;
  color: #27ae60;
}

.lottery-latest .date {
  font-size: 12px;
  color: #888;
}

.lottery-latest .balls {
  display: flex;
  gap: 5px;
  font-weight: 600;
  justify-content: center;
}

.lottery-latest .red {
  color: #e74c3c;
}

.lottery-latest .blue {
  color: #3498db;
}

.actions-section {
  text-align: center;
  margin-top: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
}

.actions-section .el-input-number {
  width: 150px;
}
</style>
