import { ref, computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useI18n } from 'vue-i18n'

export interface LogItem {
  timestamp: string
  source: string
  process_id: number
  process_name: string
  session_id: string
  instruction: string
  result: Record<string, any>
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
      'right_click': '右键点击',
      'input_text': '输入文本',
      'press_key': '按键',
      'scroll': '滚动',
      'get_process_list': '获取进程列表',
      'get_window_list': '获取窗口列表',
      'batch': '批量操作'
    },
    en_US: {
      'screenshot': 'Screenshot',
      'click': 'Click',
      'swipe': 'Swipe',
      'right_click': 'Right Click',
      'input_text': 'Input Text',
      'press_key': 'Press Key',
      'scroll': 'Scroll',
      'get_process_list': 'Get Process List',
      'get_window_list': 'Get Window List',
      'batch': 'Batch'
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
