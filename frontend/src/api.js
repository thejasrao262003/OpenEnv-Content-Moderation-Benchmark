import apiClient from './apiClient'

export const runAgent  = (taskId, seed = null) =>
  apiClient
    .post('/agent/run', seed != null ? { task_id: taskId, seed } : { task_id: taskId })
    .then(r => r.data)

export const getState  = () =>
  apiClient.get('/state').then(r => r.data)

export const getTasks  = () =>
  apiClient.get('/tasks').then(r => r.data)

export const getHealth = () =>
  apiClient.get('/health').then(r => r.data)
