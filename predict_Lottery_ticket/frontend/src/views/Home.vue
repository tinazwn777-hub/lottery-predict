<template>
  <div class="home">
    <!-- 欢迎区域 -->
    <div class="hero-section animate-fade-in">
      <h1>智能彩票预测系统</h1>
      <p>基于历史数据的统计分析，助您发现号码规律</p>
      <div class="hero-actions">
        <button class="mac-btn primary" @click="$router.push('/predict')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          开始预测
        </button>
        <button class="mac-btn secondary" @click="$router.push('/analysis')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
          </svg>
          查看分析
        </button>
      </div>
    </div>

    <!-- 特色功能卡片 -->
    <div class="features animate-fade-in" style="animation-delay: 0.1s">
      <div class="feature-card" v-for="(feature, index) in features" :key="index">
        <div class="feature-icon" v-html="feature.icon"></div>
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.desc }}</p>
      </div>
    </div>

    <!-- 快速开始 -->
    <div class="quick-start animate-fade-in" style="animation-delay: 0.2s">
      <h2>
        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        快速开始
      </h2>
      <div class="lottery-cards">
        <div
          v-for="lottery in lotteries"
          :key="lottery.code"
          class="lottery-card mac-card"
          @click="goToPredict(lottery.code)"
        >
          <div class="lottery-header">
            <h3>{{ lottery.name }}</h3>
            <span class="lottery-badge">{{ lottery.code === 'ssq' ? '双色球' : '大乐透' }}</span>
          </div>
          <p class="lottery-info">
            红球: {{ lottery.red_count }}个 | 蓝球: {{ lottery.blue_count }}个
          </p>
          <div class="lottery-latest" v-if="lottery.latest">
            <div class="latest-header">
              <span class="label">第 {{ lottery.latest.issue }} 期已开奖</span>
              <span class="date">{{ lottery.latest.open_date || '未知日期' }}</span>
            </div>
            <div class="balls">
              <span class="red" v-for="ball in lottery.latest.red_balls.split(',')" :key="'r'+ball">{{ ball }}</span>
              <span class="blue" v-for="ball in lottery.latest.blue_ball.split(',')" :key="'b'+ball">{{ ball }}</span>
            </div>
          </div>
          <div class="lottery-latest empty" v-else>
            <span class="label">暂无数据，请先刷新</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 刷新数据 -->
    <div class="actions-section animate-fade-in" style="animation-delay: 0.3s">
      <div class="refresh-controls">
        <el-input-number v-model="crawlLimit" :min="1" :max="500" size="large" />
        <button class="mac-btn success" @click="handleCrawl">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
          刷新数据
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLotteryTypes, getLatest, crawlData } from '../api'
import { ElMessage, ElLoading } from 'element-plus'

const router = useRouter()
const lotteries = ref([])
const crawlLimit = ref(50)

const features = [
  {
    icon: '<svg viewBox="0 0 24 24" width="40" height="40" fill="#007AFF"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>',
    title: '数据采集',
    desc: '自动抓取最新开奖数据，保持数据时效性'
  },
  {
    icon: '<svg viewBox="0 0 24 24" width="40" height="40" fill="#34C759"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
    title: '智能预测',
    desc: '多种统计方法结合，提供预测参考'
  },
  {
    icon: '<svg viewBox="0 0 24 24" width="40" height="40" fill="#FF9500"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>',
    title: '数据分析',
    desc: '深入分析号码频率、冷热号、奇偶比'
  }
]

const fetchData = async () => {
  try {
    const typesRes = await getLotteryTypes()
    const types = typesRes.data.types

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
    const loading = ElLoading.service({ text: '正在爬取数据...' })
    await crawlData(crawlLimit.value)
    loading.close()
    ElMessage.success(`数据刷新成功 (${crawlLimit.value}期)`)
    await fetchData()
  } catch (error) {
    ElMessage.error('数据刷新失败: ' + (error.response?.data?.detail || error.message))
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

/* 欢迎区域 */
.hero-section {
  text-align: center;
  padding: 60px 20px;
}

.hero-section h1 {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #fff 0%, #a8c0ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-section p {
  font-size: 20px;
  opacity: 0.85;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

/* macOS 风格按钮 */
.mac-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
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

.mac-btn.secondary {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.mac-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
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

/* 特色功能 */
.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin: 50px 0;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.feature-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.feature-icon {
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 18px;
  margin-bottom: 10px;
  font-weight: 600;
}

.feature-card p {
  font-size: 14px;
  opacity: 0.8;
}

/* 快速开始 */
.quick-start {
  margin-top: 50px;
}

.quick-start h2 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 28px;
  font-size: 24px;
  font-weight: 600;
}

.lottery-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.lottery-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
}

.lottery-card:hover {
  transform: scale(1.02);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.lottery-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.lottery-card h3 {
  font-size: 20px;
  color: #007AFF;
  margin: 0;
}

.lottery-badge {
  background: linear-gradient(135deg, #007AFF, #5856D6);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.lottery-info {
  color: #666;
  font-size: 13px;
  margin-bottom: 16px;
}

.lottery-latest {
  background: #f5f5f7;
  padding: 14px;
  border-radius: 10px;
}

.lottery-latest.empty {
  text-align: center;
  color: #888;
}

.latest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.latest-header .label {
  font-size: 13px;
  font-weight: 600;
  color: #34C759;
}

.latest-header .date {
  font-size: 12px;
  color: #888;
}

.latest-header .balls {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.balls {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.balls .red,
.lottery-latest .red {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  color: white;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(238, 90, 90, 0.4);
}

.balls .blue,
.lottery-latest .blue {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  color: white;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(9, 132, 227, 0.4);
}

/* 刷新数据区域 */
.actions-section {
  text-align: center;
  margin-top: 40px;
}

.refresh-controls {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.refresh-controls :deep(.el-input-number) {
  width: 120px;
}

.refresh-controls :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.9) !important;
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
