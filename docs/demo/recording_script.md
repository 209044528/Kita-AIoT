# 二阶段演示视频 / GIF 录制脚本

建议录制 60～90 秒视频，或截取其中 15～20 秒生成 GIF。

## 镜头顺序

1. 打开 `http://localhost:8001/`，展示设备、告警、工单和工作流四个区域。
2. 打开终端发布一条 MQTT 告警：

   ```powershell
   .\.venv\Scripts\python.exe scripts\mqtt_alarm_simulator.py --host localhost --count 1
   ```

3. 回到页面等待自动刷新，展示新增告警与工作流记录。
4. 打开 Dify Workflow 运行详情，展示知识检索、LLM 分析和工具调用。
5. 打开 Swagger `/docs`，展示 5 个核心 Agent 工具。
6. 打开 MinIO Console `http://localhost:9001`，展示设备文档对象。
7. 打开 `/api/v1/call-logs` 与 `/api/v1/workflow-executions` 展示可观测记录。

## 建议文件

- 视频：`docs/demo/kita-aiot-phase2.mp4`
- GIF：`docs/demo/kita-aiot-phase2.gif`
- README 展示图：`docs/screenshots/phase2_dashboard.png`

录制前请隐藏 Dify、百炼和 MinIO 的密钥。
