# API调用指令模板（AI专用）

本文档提供所有API的完整调用模板。AI在调用API时，**必须使用这些模板**，只填写参数，不要修改命令结构。

---

## 通用参数（每次调用前获取）

```bash
__API_URL__    : http://192.168.10.190:12261
__TOKEN__      : YOUR_TOKEN_HERE
__WINDOW_ID__  : WINDOW_ID_HERE
__SESSION_ID__ : my_session
__MAIN_WINDOW_ID__ : MAIN_WINDOW_ID_HERE  # 可选
```

**中文编码**：使用Unicode，如 `你好` → `\u4f60\u597d`

---

## 各API调用模板

### health（健康检查）

**优先级1：curl.exe**
```bash
curl.exe -X GET -H "Authorization: Bearer __TOKEN__" "__API_URL__/api/health"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/health" -Method GET -Headers @{"Authorization"="Bearer __TOKEN__"}
```

---

### get_window_list（获取窗口列表）

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","keyword":""}' "__API_URL__/api/get_window_list"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/get_window_list" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","keyword":""}'
```

---

### screenshot（截图）

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"coordinate_type":"grid"}' "__API_URL__/api/screenshot"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/screenshot" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"coordinate_type":"grid"}'
```

---

### click（点击）

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"x":50.0,"y":35.0}' "__API_URL__/api/click"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/click" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"x":50.0,"y":35.0}'
```

---

### input_text（输入文本）

**中文内容使用Unicode编码**

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"\u4f60\u597d"}' "__API_URL__/api/input_text"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/input_text" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"\u4f60\u597d"}'
```

---

### press_key（按键）

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"key":"ctrl c","action_method":"hijack"}' "__API_URL__/api/press_key"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/press_key" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"key":"ctrl c","action_method":"hijack"}'
```

---

### batch（批处理）

**优先级1：curl.exe**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"instructions":[{"action":"click","params":{"x":50,"y":35}},{"action":"input_text","params":{"text":"\u4f60\u597d"}}]}' "__API_URL__/api/batch"
```

**优先级2：PowerShell**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/batch" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__";"Content-Type"="application/json"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"instructions":[{"action":"click","params":{"x":50,"y":35}},{"action":"input_text","params":{"text":"\u4f60\u597d"}}]}'
```

---

## 填写规则

1. **只替换 `__XXX__` 参数**：不要修改命令的其他部分
2. **坐标使用浮点数**：`x":50.0` 而不是 `x":50`
3. **中文使用Unicode**：`你好` → `\u4f60\u597d`
4. **整行复制执行**：不要分段复制命令
5. **按优先级尝试**：优先级1失败 → 优先级2 → 报告用户

---

## 常见错误（绝对不要犯）

### 错误1：JSON引号过度转义
```bash
# 错误 ❌
curl.exe -X POST ... -d "{\"key\": \"value\"}" "URL"
# 结果：curl: (3) unmatched close brace/bracket

# 正确 ✅
curl.exe -X POST ... -d '{"key": "value"}' "URL"
```

### 错误2：PowerShell -Command模式
```powershell
# 错误 ❌
powershell -Command "Invoke-RestMethod ... -Body '{\"key\":\"value\"}'"
# 结果：ParserError: TerminatorExpectedAtEndOfString

# 正确 ✅ - 使用.ps1脚本，不要用-Command模式
powershell -ExecutionPolicy Bypass -File script.ps1 arg1 arg2
```

### 错误3：Heredoc语法
```bash
# 错误 ❌
curl ... -d @- <<'EOF'
{"key": "value"}
EOF
# 结果：语法不稳定，某些环境会失败

# 正确 ✅ - 直接使用单行命令
curl.exe -X POST ... -d '{"key": "value"}' "URL"
```

**关键规则**：
- JSON内部的双引号不需要转义：`{"key":"value"}` 是正确的
- 不要使用 `\"` 这种转义，除非是在特定语言字符串内部
- 整个JSON用单引号包围（在curl命令中）

---

## 中文常用Unicode编码

| 中文 | Unicode编码 |
|------|-------------|
| 你好 | `\u4f60\u597d` |
| 是 | `\u662f` |
| 的 | `\u7684` |
| 确定 | `\u786e\u5b9a` |
| 取消 | `\u53d6\u6d88` |
| 输入 | `\u8f93\u5165` |
| 删除 | `\u5220\u9664` |
| 保存 | `\u4fdd\u5b58` |
| | `\n` (换行) |

**生成方法**：
- Python: `"你好".encode('unicode_escape').decode('utf-8')` → `\\u4f60\\u597d`
- JavaScript: `JSON.stringify("你好")` → `"\u4f60\u597d"`
- AI：大多数AI会自动生成Unicode编码

---

## 坑点（常见陷阱）

### API调用相关

- ⚠️ **坐标系统**：使用网格坐标系统，从截图的网格标记中直接读出数字即可
- ⚠️ **window_id**：必须从 `get_window_list` 获取，不能猜测
- ⚠️ **session_id格式**：使用下划线分隔，不要用连字符（如 `app_date_timestamp`）
- ⚠️ **本地vs远程**：截图API返回格式不同，本地返回 `image_path`，远程返回 `image_base64`

### 截图相关

- ⚠️ **中文目录名**：某些环境下中文目录名可能创建失败，脚本会自动fallback到时间戳目录名
- ⚠️ **coordinate_type**：默认使用 `grid` 获取网格坐标，便于定位

### 输入相关

- ⚠️ **中文编码**：必须使用Unicode编码，否则会乱码
- ⚠️ **焦点问题**：如果输入无效，可能需要先点击输入框位置激活焦点

### 窗口相关

- ⚠️ **主窗口vs子窗口**：输入、按键类操作通常需要子窗口，点击类通常主窗口可工作
- ⚠️ **include_children**：获取窗口列表时加上此参数可获取子窗口

### 操作模式

- ⚠️ **background模式**：某些应用（特别是UWP应用）可能不响应
- ⚠️ **hijack模式**：会短暂激活目标窗口，需要用户确认

### 批处理

- ⚠️ **instructions数组**：每个instruction必须包含 `action` 和 `params` 字段
- ⚠️ **顺序执行**：批处理中的指令按顺序依次执行
