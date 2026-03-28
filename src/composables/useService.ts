import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

export interface ServiceStatus {
  is_running: boolean
  port: number
  local_ip: string
  token: string
}

const status = ref<ServiceStatus>({
  is_running: false,
  port: 12261,
  local_ip: '127.0.0.1',
  token: ''
})

export function useService() {
  const loadStatus = async () => {
    try {
      const result = await invoke<ServiceStatus>('get_service_status')
      status.value = result
    } catch (error) {
      console.error('Failed to load service status:', error)
    }
  }

  const toggleService = async () => {
    try {
      if (status.value.is_running) {
        await invoke('stop_service')
      } else {
        await invoke('start_service')
      }
      await loadStatus()
    } catch (error) {
      console.error('Failed to toggle service:', error)
    }
  }

  const copyToken = () => {
    navigator.clipboard.writeText(status.value.token)
  }

  const regenerateToken = async () => {
    try {
      const newToken = await invoke<string>('regenerate_token')
      status.value.token = newToken
    } catch (error) {
      console.error('Failed to regenerate token:', error)
    }
  }

  return {
    status,
    loadStatus,
    toggleService,
    copyToken,
    regenerateToken
  }
}
