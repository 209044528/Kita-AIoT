# 阿里云百炼二阶段基础接入

二阶段将百炼作为备用平台，通过 OpenAI 兼容接口完成基础连通。

## 配置

在阿里云百炼控制台创建 API Key，然后写入 `.env`：

```env
BAILIAN_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
BAILIAN_API_KEY=sk-xxxxxxxx
BAILIAN_MODEL=qwen-plus
```

## 连通测试

启动 FastAPI 后调用：

```powershell
$body = @{ message = "请用一句话说明设备高温告警的首要排查项" } | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/api/v1/platforms/bailian/test `
  -ContentType application/json `
  -Body $body
```

返回百炼的 Chat Completions 响应即表示基础接入成功。

建议保存以下截图到 `docs/screenshots/`：

- `bailian_api_key.png`：API Key 配置页，必须遮挡密钥。
- `bailian_connection_test.png`：接口连通响应。

当前百炼不参与 MQTT 自动工作流；它作为二阶段的第二平台基础接入，后续可切换为主分析平台。
