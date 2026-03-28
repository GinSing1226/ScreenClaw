import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

export interface AppConfig {
  server: {
    port: number
    host: string
    token: string
    local_ip: string
    auto_start: boolean
    service_enabled: boolean
  }
  screenshot: {
    default_coordinate_type: string
    default_grid_density: number
    default_grid_color: string
    default_grid_opacity: number
    default_number_density: number
    default_number_decimal: number
    default_number_size: number
    default_number_color: string
    default_number_opacity: number
    image_quality: number
    max_image_width: number
  }
  input: {
    newline_mapping: Record<string, string>
  }
  security: {
    blocked_processes: string[]
    auto_confirm_processes: string[]
  }
  log: {
    retention_days: number
  }
  ui: {
    language: string
  }
}

export interface SettingsForm {
  port: number
  gridDensity: number
  gridColor: string
  gridOpacity: number
  numberDensity: number
  numberDecimal: number
  numberSize: number
  numberColor: string
  numberOpacity: number
  imageQuality: number
  maxImageWidth: number
  blockedProcesses: string
  autoConfirmProcesses: string
  language: string
  autoStart: boolean
}

const config = ref<AppConfig | null>(null)
const settingsForm = ref<SettingsForm>({
  port: 12261,
  gridDensity: 5,
  gridColor: '#00FF00',
  gridOpacity: 50,
  numberDensity: 2,
  numberDecimal: 0,
  numberSize: 8,
  numberColor: '#00FF00',
  numberOpacity: 100,
  imageQuality: 85,
  maxImageWidth: 1920,
  blockedProcesses: '',
  autoConfirmProcesses: '',
  language: 'zh_CN',
  autoStart: false
})

const configSaving = ref(false)
const configMessage = ref('')

export function useConfig() {
  const loadConfig = async () => {
    try {
      const result = await invoke<AppConfig>('get_config')
      config.value = result
      settingsForm.value = {
        port: result.server.port,
        gridDensity: result.screenshot.default_grid_density,
        gridColor: result.screenshot.default_grid_color,
        gridOpacity: result.screenshot.default_grid_opacity,
        numberDensity: result.screenshot.default_number_density ?? 2,
        numberDecimal: result.screenshot.default_number_decimal ?? 0,
        numberSize: result.screenshot.default_number_size ?? 8,
        numberColor: result.screenshot.default_number_color ?? '#00FF00',
        numberOpacity: result.screenshot.default_number_opacity ?? 100,
        imageQuality: result.screenshot.image_quality,
        maxImageWidth: result.screenshot.max_image_width,
        blockedProcesses: result.security.blocked_processes.join('\n'),
        autoConfirmProcesses: result.security.auto_confirm_processes.join('\n'),
        language: result.ui.language,
        autoStart: result.server.auto_start
      }
    } catch (error) {
      console.error('Failed to load config:', error)
    }
  }

  const saveConfig = async () => {
    configSaving.value = true
    configMessage.value = ''
    try {
      const newConfig: AppConfig = {
        server: {
          port: settingsForm.value.port,
          auto_start: settingsForm.value.autoStart,
          token: config.value?.server?.token || '',
          host: config.value?.server?.host || '0.0.0.0',
          local_ip: config.value?.server?.local_ip || '127.0.0.1',
          service_enabled: true
        },
        screenshot: {
          default_coordinate_type: 'grid',
          default_grid_density: settingsForm.value.gridDensity,
          default_grid_color: settingsForm.value.gridColor,
          default_grid_opacity: settingsForm.value.gridOpacity,
          default_number_density: settingsForm.value.numberDensity,
          default_number_decimal: settingsForm.value.numberDecimal,
          default_number_size: settingsForm.value.numberSize,
          default_number_color: settingsForm.value.numberColor,
          default_number_opacity: settingsForm.value.numberOpacity,
          image_quality: settingsForm.value.imageQuality,
          max_image_width: settingsForm.value.maxImageWidth
        },
        input: {
          newline_mapping: {}
        },
        security: {
          blocked_processes: settingsForm.value.blockedProcesses
            .split('\n')
            .map(p => p.trim())
            .filter(p => p),
          auto_confirm_processes: settingsForm.value.autoConfirmProcesses
            .split('\n')
            .map(p => p.trim())
            .filter(p => p)
        },
        log: {
          retention_days: 0
        },
        ui: {
          language: settingsForm.value.language
        }
      }
      await invoke('update_config', { newConfig })
      configMessage.value = '保存成功 ✓'
      setTimeout(() => { configMessage.value = '' }, 2000)
    } catch (error) {
      configMessage.value = String(error)
    } finally {
      configSaving.value = false
    }
  }

  const resetConfig = () => {
    if (config.value) {
      settingsForm.value = {
        port: 12261,
        gridDensity: 5,
        gridColor: '#00FF00',
        gridOpacity: 50,
        numberDensity: 2,
        numberDecimal: 0,
        numberSize: 8,
        numberColor: '#00FF00',
        numberOpacity: 100,
        imageQuality: 85,
        maxImageWidth: 1920,
        blockedProcesses: config.value.security.blocked_processes.join('\n'),
        autoConfirmProcesses: config.value.security.auto_confirm_processes.join('\n'),
        language: config.value.ui.language,
        autoStart: false
      }
    }
  }

  return {
    config,
    settingsForm,
    configSaving,
    configMessage,
    loadConfig,
    saveConfig,
    resetConfig
  }
}
