import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import './style.css'

// 国际化配置
const i18n = createI18n({
  legacy: false,
  locale: 'zh_CN',
  fallbackLocale: 'en_US',
  messages: {
    zh_CN: {
      app: {
        title: 'ScreenClaw',
        monitoring: '监控面板',
        settings: '系统设置'
      },
      service: {
        status: '服务状态',
        running: '运行中',
        stopped: '已停止',
        start: '启动服务',
        stop: '停止服务',
        localAddress: '本机地址',
        lanAddress: '局域网地址',
        token: 'Token'
      },
      logs: {
        title: '指令日志',
        filter: '筛选',
        search: '搜索',
        keyword: '关键词',
        aiApp: 'AI应用',
        session: '会话',
        date: '日期',
        time: '时间',
        process: '进程',
        instruction: '指令',
        result: '结果',
        duration: '耗时',
        success: '成功',
        failed: '失败',
        viewDetails: '查看详情'
      },
      settings: {
        title: '系统设置',
        server: {
          title: '服务配置',
          port: '端口',
          token: 'Token',
          regenerate: '重新生成'
        },
        screenshot: {
          title: '截图默认值',
          gridDensity: '网格密度',
          gridColor: '网格颜色',
          gridOpacity: '网格透明度',
          imageQuality: '图片质量',
          maxImageWidth: '最大图片宽度'
        },
        security: {
          title: '安全设置',
          blockedProcesses: '禁止访问进程',
          addProcess: '添加进程'
        },
        ui: {
          title: '界面设置',
          language: '语言',
          autoStart: '开机自启动'
        },
        save: '保存配置',
        reset: '恢复默认'
      },
      confirm: {
        title: '操作确认',
        message: 'ScreenClaw 需要临时控制你的键盘和鼠标',
        process: '目标进程',
        source: '指令来源',
        allow: '允许',
        cancel: '取消'
      },
      common: {
        save: '保存',
        cancel: '取消',
        confirm: '确认',
        close: '关闭',
        copy: '复制'
      }
    },
    en_US: {
      app: {
        title: 'ScreenClaw',
        monitoring: 'Monitor',
        settings: 'Settings'
      },
      service: {
        status: 'Service Status',
        running: 'Running',
        stopped: 'Stopped',
        start: 'Start Service',
        stop: 'Stop Service',
        localAddress: 'Local Address',
        lanAddress: 'LAN Address',
        token: 'Token'
      },
      logs: {
        title: 'Instruction Logs',
        filter: 'Filter',
        search: 'Search',
        keyword: 'Keyword',
        aiApp: 'AI App',
        session: 'Session',
        date: 'Date',
        time: 'Time',
        process: 'Process',
        instruction: 'Instruction',
        result: 'Result',
        duration: 'Duration',
        success: 'Success',
        failed: 'Failed',
        viewDetails: 'View Details'
      },
      settings: {
        title: 'Settings',
        server: {
          title: 'Server Config',
          port: 'Port',
          token: 'Token',
          regenerate: 'Regenerate'
        },
        screenshot: {
          title: 'Screenshot Defaults',
          gridDensity: 'Grid Density',
          gridColor: 'Grid Color',
          gridOpacity: 'Grid Opacity',
          imageQuality: 'Image Quality',
          maxImageWidth: 'Max Image Width'
        },
        security: {
          title: 'Security',
          blockedProcesses: 'Blocked Processes',
          addProcess: 'Add Process'
        },
        ui: {
          title: 'UI Settings',
          language: 'Language',
          autoStart: 'Auto Start on Boot'
        },
        save: 'Save',
        reset: 'Reset'
      },
      confirm: {
        title: 'Confirm Operation',
        message: 'ScreenClaw needs to temporarily control your keyboard and mouse',
        process: 'Target Process',
        source: 'Source',
        allow: 'Allow',
        cancel: 'Cancel'
      },
      common: {
        save: 'Save',
        cancel: 'Cancel',
        confirm: 'Confirm',
        close: 'Close',
        copy: 'Copy'
      }
    }
  }
})

const app = createApp(App)
app.use(i18n)
app.mount('#app')
