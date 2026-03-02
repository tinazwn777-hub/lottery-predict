import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 获取支持的彩种
export const getLotteryTypes = () => api.get('/lottery/types')

// 获取历史数据
export const getHistory = (type, limit = 50, offset = 0) =>
  api.get(`/lottery/${type}/history`, { params: { limit, offset } })

// 获取最新一期
export const getLatest = (type) => api.get(`/lottery/${type}/latest`)

// 爬取数据
export const crawlData = (limit = 50) => api.post('/lottery/crawl', {}, { params: { limit } })

// 生成预测
export const predict = (type, method = 'frequency', count = 1) =>
  api.post('/lottery/predict', { lottery_type: type, method, count })

// 获取统计数据
export const getStatistics = (type) => api.get(`/lottery/statistics/${type}`)

// 清空数据
export const clearData = (type) => api.delete(`/lottery/${type}/clear`)

// ==================== 预测保存与验证API ====================

// 保存预测号码
export const savePredictions = (lotteryType, predictions) =>
  api.post('/lottery/predictions', { lottery_type: lotteryType, predictions })

// 获取预测列表
export const getPredictions = (lotteryType) =>
  api.get(`/lottery/predictions/${lotteryType}`)

// 获取所有预测记录
export const getAllPredictions = () =>
  api.get('/lottery/predictions')

// 清空预测记录
export const clearPredictions = (lotteryType) =>
  api.delete(`/lottery/predictions/${lotteryType}`)

// 验证预测号码
export const verifyPredictions = (lotteryType, limit = 100) =>
  api.post('/lottery/verify', { lottery_type: lotteryType, limit })

// 获取验证统计
export const getVerificationStats = (lotteryType) =>
  api.get(`/lottery/verification-stats/${lotteryType}`)
