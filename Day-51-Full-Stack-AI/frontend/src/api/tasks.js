// frontend/src/api/tasks.js
import client from './client'

export const listTasks = (params) =>
  client.get('/tasks', { params }).then((r) => r.data)

export const createTask = (data) =>
  client.post('/tasks', data).then((r) => r.data)

export const getTask = (id) =>
  client.get(`/tasks/${id}`).then((r) => r.data)

export const updateTask = (id, data) =>
  client.patch(`/tasks/${id}`, data).then((r) => r.data)

export const deleteTask = (id) =>
  client.delete(`/tasks/${id}`)