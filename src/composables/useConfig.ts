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
    default_color_mode: string
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
  delegated: {
    active: boolean
    exit_hotkey: string
  }
  scroll_screenshot?: {
    max_scrolls: number
    max_scroll_wait: number
    max_timeout: number
    default_scroll_percent: number
    default_scroll_wait: number
    max_adjust_retries: number
    target_overlap_min: number
    target_overlap_max: number
    stop_threshold: number
    image_quality: number
  }
}

export interface SettingsForm {
  port: number
  colorMode: string
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
  exitHotkey: string
  // 滚动长截图
  maxScrolls: number
  maxScrollWait: number
  maxTimeout: number
  defaultScrollPercent: number
  defaultScrollWait: number
  maxAdjustRetries: number
  targetOverlapMin: number
  targetOverlapMax: number
  stopThreshold: number
  scrollImageQuality: number
}

const config = ref<AppConfig | null>(null)
const settingsForm = ref<SettingsForm>({
  port: 12261,
  colorMode: 'grayscale',
  gridDensity: 5,
  gridColor: '#ff0000',
  gridOpacity: 50,
  numberDensity: 2,
  numberDecimal: 0,
  numberSize: 12,
  numberColor: '#ff0000',
  numberOpacity: 100,
  imageQuality: 85,
  maxImageWidth: 1920,
  blockedProcesses: '',
  autoConfirmProcesses: '',
  language: 'zh_CN',
  autoStart: false,
  exitHotkey: 'ctrl+alt+z',
  // 滚动长截图
  maxScrolls: 5,
  maxScrollWait: 30,
  maxTimeout: 60,
  defaultScrollPercent: 0.85,
  defaultScrollWait: 1.0,
  maxAdjustRetries: 4,
  targetOverlapMin: 0.35,
  targetOverlapMax: 0.45,
  stopThreshold: 0.0001,
  scrollImageQuality: 95
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
        colorMode: result.screenshot?.default_color_mode ?? 'grayscale',
        gridDensity: result.screenshot?.default_grid_density ?? 5,
        gridColor: result.screenshot?.default_grid_color ?? '#ff0000',
        gridOpacity: result.screenshot?.default_grid_opacity ?? 50,
        numberDensity: result.screenshot?.default_number_density ?? 2,
        numberDecimal: result.screenshot?.default_number_decimal ?? 0,
        numberSize: result.screenshot?.default_number_size ?? 12,
        numberColor: result.screenshot?.default_number_color ?? '#ff0000',
        numberOpacity: result.screenshot?.default_number_opacity ?? 100,
        imageQuality: result.screenshot?.image_quality ?? 85,
        maxImageWidth: result.screenshot?.max_image_width ?? 1920,
        blockedProcesses: (result.security?.blocked_processes || []).join('\n'),
        autoConfirmProcesses: (result.security?.auto_confirm_processes || []).join('\n'),
        language: result.ui?.language ?? 'zh_CN',
        autoStart: result.server?.auto_start ?? false,
        exitHotkey: result.delegated?.exit_hotkey || 'ctrl+alt+z',
        // 滚动长截图
        maxScrolls: result.scroll_screenshot?.max_scrolls ?? 5,
        maxScrollWait: result.scroll_screenshot?.max_scroll_wait ?? 30,
        maxTimeout: result.scroll_screenshot?.max_timeout ?? 60,
        defaultScrollPercent: result.scroll_screenshot?.default_scroll_percent ?? 0.85,
        defaultScrollWait: result.scroll_screenshot?.default_scroll_wait ?? 1.0,
        maxAdjustRetries: result.scroll_screenshot?.max_adjust_retries ?? 4,
        targetOverlapMin: result.scroll_screenshot?.target_overlap_min ?? 0.35,
        targetOverlapMax: result.scroll_screenshot?.target_overlap_max ?? 0.45,
        stopThreshold: result.scroll_screenshot?.stop_threshold ?? 0.0001,
        scrollImageQuality: result.scroll_screenshot?.image_quality ?? 95
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
          default_color_mode: settingsForm.value.colorMode,
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
        },
        delegated: {
          active: config.value?.delegated?.active || false,
          exit_hotkey: settingsForm.value.exitHotkey
        },
        scroll_screenshot: {
          max_scrolls: settingsForm.value.maxScrolls,
          max_scroll_wait: settingsForm.value.maxScrollWait,
          max_timeout: settingsForm.value.maxTimeout,
          default_scroll_percent: settingsForm.value.defaultScrollPercent,
          default_scroll_wait: settingsForm.value.defaultScrollWait,
          max_adjust_retries: settingsForm.value.maxAdjustRetries,
          target_overlap_min: settingsForm.value.targetOverlapMin,
          target_overlap_max: settingsForm.value.targetOverlapMax,
          stop_threshold: settingsForm.value.stopThreshold,
          image_quality: settingsForm.value.scrollImageQuality
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
        colorMode: 'grayscale',
        gridDensity: 5,
        gridColor: '#ff0000',
        gridOpacity: 50,
        numberDensity: 2,
        numberDecimal: 0,
        numberSize: 12,
        numberColor: '#ff0000',
        numberOpacity: 100,
        imageQuality: 85,
        maxImageWidth: 1920,
        blockedProcesses: config.value.security.blocked_processes.join('\n'),
        autoConfirmProcesses: config.value.security.auto_confirm_processes.join('\n'),
        language: config.value.ui.language,
        autoStart: false,
        exitHotkey: config.value.delegated?.exit_hotkey || 'ctrl+alt+z',
        // 滚动长截图
        maxScrolls: 5,
        maxScrollWait: 30,
        maxTimeout: 60,
        defaultScrollPercent: 0.85,
        defaultScrollWait: 1.0,
        maxAdjustRetries: 4,
        targetOverlapMin: 0.35,
        targetOverlapMax: 0.45,
        stopThreshold: 0.0001,
        scrollImageQuality: 95
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
