import { ref, computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useI18n } from 'vue-i18n'

export interface LogItem {
  timestamp: string
  source: string
  client_ip: string
  process_id: number
  process_name: string
  session_id: string
  instruction: string
  params: Record<string, any>
  result: Record<string, any>
  duration_ms: number
}

export interface LogFilter {
  aiApp: string
  targetApp: string
  session: string
  date: string
}

const logs = ref<LogItem[]>([])
const logsLoading = ref(false)
const filter = ref<LogFilter>({
  aiApp: '',
  targetApp: '',
  session: '',
  date: ''
})
const searchKeyword = ref('')

export function useLogs() {
  const { locale } = useI18n()

  // 指令类型翻译映射
  const instructionTranslations: Record<string, Record<string, string>> = {
    zh_CN: {
      'screenshot': '截图',
      'click': '点击',
      'swipe': '滑动',
      'drag': '拖拽',
      'right_click': '右键点击',
      'input_text': '输入文本',
      'press_key': '按键',
      'scroll': '滚动',
      'long_press': '长按',
      'hover': '悬浮',
      'wait': '等待',
      'get_process_list': '获取进程列表',
      'get_window_list': '获取窗口列表',
      'batch': '批量操作',
      'scroll_screenshot': '滚动长截图',
      'crop_zoom_screenshot': '裁剪放大',
      'delegated_enter': '进入托管',
      'delegated_exit': '退出托管',
      'delegated_status': '查询托管状态',
      // 桌面级操作
      'desktop_screenshot': '桌面截图',
      'desktop_click': '桌面点击',
      'desktop_double_click': '桌面双击',
      'desktop_right_click': '桌面右键',
      'desktop_drag': '桌面拖拽',
      'desktop_scroll': '桌面滚动',
      'desktop_input_text': '桌面输入文本',
      'desktop_press_key': '桌面按键',
      'desktop_hover': '桌面悬浮',
    },
    en_US: {
      'screenshot': 'Screenshot',
      'click': 'Click',
      'swipe': 'Swipe',
      'drag': 'Drag',
      'right_click': 'Right Click',
      'input_text': 'Input Text',
      'press_key': 'Press Key',
      'scroll': 'Scroll',
      'long_press': 'Long Press',
      'hover': 'Hover',
      'wait': 'Wait',
      'get_process_list': 'Get Process List',
      'get_window_list': 'Get Window List',
      'batch': 'Batch',
      'scroll_screenshot': 'Scroll Screenshot',
      'crop_zoom_screenshot': 'Crop Zoom',
      'delegated_enter': 'Enter Delegated',
      'delegated_exit': 'Exit Delegated',
      'delegated_status': 'Query Delegated Status',
      // Desktop operations
      'desktop_screenshot': 'Desktop Screenshot',
      'desktop_click': 'Desktop Click',
      'desktop_double_click': 'Desktop Double Click',
      'desktop_right_click': 'Desktop Right Click',
      'desktop_drag': 'Desktop Drag',
      'desktop_scroll': 'Desktop Scroll',
      'desktop_input_text': 'Desktop Input Text',
      'desktop_press_key': 'Desktop Press Key',
      'desktop_hover': 'Desktop Hover',
    }
  }

  const translateInstruction = (instruction: string): string => {
    const translations = instructionTranslations[locale.value] || instructionTranslations.zh_CN
    return translations[instruction] || instruction
  }

  const uniqueAiApps = computed(() => {
    const names = new Set<string>()
    logs.value.forEach(log => {
      if (log.source) names.add(log.source)
    })
    return Array.from(names).sort()
  })

  const uniqueTargetApps = computed(() => {
    const names = new Set<string>()
    logs.value.forEach(log => {
      if (log.process_name) names.add(log.process_name)
    })
    return Array.from(names).sort()
  })

  const filteredLogs = computed(() => {
    return logs.value.filter(log => {
      if (filter.value.aiApp && log.source !== filter.value.aiApp) return false
      if (filter.value.targetApp && log.process_name !== filter.value.targetApp) return false
      if (filter.value.session) {
        if (!log.session_id || !log.session_id.toLowerCase().includes(filter.value.session.toLowerCase())) {
          return false
        }
      }
      if (filter.value.date) {
        const logDate = new Date(log.timestamp).toISOString().split('T')[0]
        if (logDate !== filter.value.date) return false
      }
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase()
        const matchInstruction = log.instruction?.toLowerCase().includes(keyword)
        const matchProcess = log.process_name?.toLowerCase().includes(keyword)
        if (!matchInstruction && !matchProcess) return false
      }
      return true
    })
  })

  const loadLogs = async () => {
    logsLoading.value = true
    try {
      const result = await invoke<LogItem[]>('get_logs')
      logs.value = result
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      logsLoading.value = false
    }
  }

  const clearFilters = () => {
    filter.value = { aiApp: '', targetApp: '', session: '', date: '' }
    searchKeyword.value = ''
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return {
    logs,
    logsLoading,
    filter,
    searchKeyword,
    uniqueAiApps,
    uniqueTargetApps,
    filteredLogs,
    loadLogs,
    clearFilters,
    translateInstruction,
    formatTime
  }
}
