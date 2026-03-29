# API调用模板（降级方案）

> ⚠️ **优先使用脚本，无需手动组装curl！**
>
> ## 脚本分工
> - **截图API** → `scripts/fetch_screenshot_cli.py`（专用脚本，处理base64响应）
> - **其他所有API** → `scripts/api_call.py`（通用脚本）
>
> 本文档仅在脚本无法使用时作为参考。

---

## 优先使用脚本 ⭐

**AI应该优先调用：**
```bash
python scripts/api_call.py __API_URL__ __TOKEN__ <endpoint> __AI_APP_TYPE__ [参数...]
```

**示例：**
```bash
# 获取窗口列表（直接传中文）
python scripts/api_call.py http://192.168.10.190:12261 TOKEN get_window_list claude_code keyword=飞书

# 输入文本
python scripts/api_call.py http://192.168.10.190:12261 TOKEN input_text claude_code window_id=123456 text=你好世界
```

**中文处理**：直接传中文即可，脚本会自动转Unicode！

**降级路径**（按顺序尝试）：
1. `api_call.py`（Python版，推荐）
2. `api_call.ps1`（PowerShell版，需UTF-8启动）
3. `api_call.sh`（Bash版）
4. 手动curl（见下方模板）

**注意**：
- 可以先检测python环境，存在python再尝试。
- 如果python执行失败，不要尝试解决python环境问题，直接降级执行。
---

## 通用参数

```bash
__API_URL__    : http://192.168.10.190:12261
__TOKEN__      : YOUR_TOKEN_HERE
__WINDOW_ID__  : WINDOW_ID_HERE
__SESSION_ID__ : my_session
__AI_APP_TYPE__ : claude_code
```

---

## 手动curl模板（脚本失败时的降级方案）

### 健康检查

```bash
curl.exe -X GET -H "Authorization: Bearer __TOKEN__" "__API_URL__/api/health"
```

### 获取窗口列表

```bash
# 无关键词
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","keyword":""}' "__API_URL__/api/get_window_list"

# 有关键词（中文需Unicode）
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","keyword":"\u98de\u4e66"}' "__API_URL__/api/get_window_list"
```

### 截图

```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"coordinate_type":"grid"}' "__API_URL__/api/screenshot"
```

### 点击

```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"x":50.0,"y":35.0}' "__API_URL__/api/click"
```

### 输入文本

```bash
# 英文
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"hello"}' "__API_URL__/api/input_text"

# 中文（需Unicode）
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"\u4f60\u597d"}' "__API_URL__/api/input_text"
```

### 按键

```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"key":"ctrl c","action_method":"hijack"}' "__API_URL__/api/press_key"
```

### 批处理

```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"__AI_APP_TYPE__","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"instructions":[{"action":"click","params":{"x":50,"y":35}},{"action":"input_text","params":{"text":"\u4f60\u597d"}}]}' "__API_URL__/api/batch"
```

---

## 常见错误

### 错误1：JSON引号过度转义
```bash
# ❌ 错误
curl.exe ... -d "{\"key\": \"value\"}"
# ✅ 正确
curl.exe ... -d '{"key": "value"}'
```

### 错误2：PowerShell -Command模式
```powershell
# ❌ 错误
powershell -Command "Invoke-RestMethod ... -Body '{\"key\":\"value\"}'"
# ✅ 正确 - 使用脚本
python scripts/api_call.py ...
```

### 错误3：中文输入
- 手动curl时中文必须使用Unicode编码
- 使用api_call.py脚本时直接传中文即可
