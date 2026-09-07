// frontend/src/api/ai.js
import client from './client'

export const analyzeTask = (title, description) =>
  client.post('/ai/analyze', { title, description }).then((r) => r.data)

export const expandTask = (title) =>
  client.post('/ai/expand', { title }).then((r) => r.data)

export const breakdownTask = (title, description) =>
  client.post('/ai/breakdown', { title, description }).then((r) => r.data)

export const weeklySummary = () =>
  client.get('/ai/weekly-summary').then((r) => r.data)