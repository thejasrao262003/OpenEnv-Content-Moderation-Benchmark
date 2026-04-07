import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const runAgent  = (taskId, seed = null) =>
  api.post('/agent/run', seed != null ? { task_id: taskId, seed } : { task_id: taskId }).then(r => r.data)

export const getState  = () =>
  api.get('/state').then(r => r.data)

export const getTasks  = () =>
  api.get('/tasks').then(r => r.data)

export const getHealth = () =>
  api.get('/health').then(r => r.data)
