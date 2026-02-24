import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Predict from './views/Predict.vue'
import Analysis from './views/Analysis.vue'
import Verify from './views/Verify.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/predict',
    name: 'Predict',
    component: Predict
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  },
  {
    path: '/verify',
    name: 'Verify',
    component: Verify
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
