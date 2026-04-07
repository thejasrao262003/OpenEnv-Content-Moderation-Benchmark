import axios from 'axios'

const DEFAULT_TIMEOUT_MS = 15000

const trimTrailingSlash = (value = '') => value.replace(/\/+$/, '')

const getApiBaseUrl = () => {
  if (import.meta.env.DEV) {
    return '/api'
  }

  const configuredUrl = trimTrailingSlash(import.meta.env.VITE_API_URL || '')
  if (!configuredUrl) {
    throw new Error('Missing VITE_API_URL in production environment')
  }

  return configuredUrl
}

const getTimeoutMs = () => {
  const raw = Number(import.meta.env.VITE_API_TIMEOUT_MS)
  return Number.isFinite(raw) && raw > 0 ? raw : DEFAULT_TIMEOUT_MS
}

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: getTimeoutMs(),
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

export const getApiBaseUrlLabel = () =>
  import.meta.env.DEV ? 'proxy (/api)' : trimTrailingSlash(import.meta.env.VITE_API_URL || '')

export const toApiErrorMessage = (error, fallback = 'Failed to connect to API') => {
  if (error?.code === 'ECONNABORTED') {
    return `Request timed out after ${getTimeoutMs()}ms`
  }

  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  )
}

export default apiClient