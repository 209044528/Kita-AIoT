# Kita-AIoT：设备运维智能体工作流系统

Kita-AIoT 是一个面向 AIoT 场景的设备运维智能体工作流 Demo。项目基于 Dify / 阿里百炼等 AI 应用开发平台，结合 FastAPI、MQTT、PostgreSQL、Redis、MinIO 等后端组件，模拟设备告警上报、知识库检索、故障原因分析、处理建议生成与工单流转的智能运维闭环。

本项目主要用于探索 AI Agent、RAG 知识库、工作流编排与 AIoT 设备运维场景的结合方式。

---

## 1. 项目背景

在 AIoT 设备运维场景中，设备数量多、告警类型复杂、处理流程依赖人工经验，常见问题包括：

* 设备告警信息分散，人工排查效率较低；
* 故障处理依赖说明书、SOP、历史工单等文档资料；
* 运维人员需要频繁查询设备状态、历史告警和处理记录；
* 告警分析、知识检索、工单创建等流程缺少自动化串联。

因此，本项目尝试将大模型智能体引入设备运维流程，通过 Agent 工具调用、RAG 知识库检索和自动化工作流编排，实现从“设备告警”到“故障分析”和“工单生成”的自动化处理。

---

## 2. 核心功能

### 2.1 设备运维智能体

基于 Dify / 阿里百炼搭建设备运维智能体，围绕设备告警分析、知识库检索、处理建议生成和工单流转设计自动化工作流。

智能体支持：

* 根据用户问题识别意图；
* 自动调用设备状态查询工具；
* 检索设备知识库和历史工单；
* 生成故障原因分析；
* 输出结构化处理建议；
* 在需要时创建运维工单。

---

### 2.2 企业知识库 RAG

项目构建设备运维知识库，接入以下类型的资料：

* 设备说明书；
* 故障排查手册；
* 运维 SOP；
* 历史告警记录；
* 历史工单数据；
* 常见问题 FAQ。

知识库能力包括：

* 文档切分；
* 向量检索；
* 相似度过滤；
* 知识来源引用；
* 面向故障诊断场景的 Prompt 组装。

---

### 2.3 FastAPI 工具服务

项目使用 FastAPI 封装设备运维相关工具接口，供智能体工作流调用。

主要工具包括：

| 工具名称   | 功能说明                         |
| ------ | ---------------------------- |
| 查询设备状态 | 根据设备 ID 查询在线状态、运行状态、电量、温度等信息 |
| 查询历史告警 | 查询设备最近一段时间内的告警记录             |
| 检索知识库  | 根据问题或告警内容检索相关说明书、SOP 或 FAQ   |
| 创建工单   | 根据分析结果自动生成运维工单               |
| 查询工单   | 查询设备相关的历史处理记录                |

---

### 2.4 MQTT 告警模拟

项目通过 MQTT 模拟 AIoT 设备告警上报流程。

告警链路如下：

```text
设备模拟器
  → MQTT Broker
  → FastAPI 告警接收服务
  → PostgreSQL 告警落库
  → 智能体工作流分析
  → RAG 知识库检索
  → 生成故障原因与处理建议
  → 创建运维工单
```

---

### 2.5 Prompt 模板优化

针对不同业务场景，项目设计了多类 Prompt 模板：

* 故障诊断 Prompt；
* 知识库问答 Prompt；
* 工单生成 Prompt；
* 设备状态分析 Prompt；
* 运维建议生成 Prompt。

目标是提升大模型回答的结构化程度、知识引用准确性和业务可用性。

---

## 3. 技术栈

| 类型      | 技术                    |
| ------- | --------------------- |
| AI 应用平台 | Dify、阿里百炼             |
| 后端服务    | Python、FastAPI        |
| 消息通信    | MQTT                  |
| 数据库     | PostgreSQL            |
| 缓存      | Redis                 |
| 对象存储    | MinIO                 |
| 知识库     | Embedding、向量检索、RAG    |
| 部署      | Docker、Docker Compose |

---

## 4. 系统架构

```text
┌──────────────────────┐
│    AIoT 设备模拟器    │
│  模拟温度/电量/离线告警│
└───────────┬──────────┘
            │ MQTT
            ▼
┌──────────────────────┐
│      MQTT Broker     │
└───────────┬──────────┘
            │
            ▼
┌──────────────────────┐
│    FastAPI 后端服务   │
│  设备 / 告警 / 工单接口│
└───────┬───────┬──────┘
        │       │
        ▼       ▼
┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │
│业务数据存储│ │缓存/会话 │
└──────────┘ └──────────┘
        │
        ▼
┌──────────────────────┐
│  Dify / 阿里百炼工作流 │
│ 意图识别 / 工具调用 / RAG│
└───────────┬──────────┘
            │
            ▼
┌──────────────────────┐
│      设备知识库        │
│ 说明书 / SOP / FAQ / 工单│
└──────────────────────┘
```

---

## 5. 工作流设计

### 5.1 告警分析流程

```text
1. 设备通过 MQTT 上报告警
2. 后端服务接收告警并写入数据库
3. 智能体读取告警内容
4. 根据设备 ID 查询设备状态
5. 查询该设备历史告警
6. 检索设备知识库中的相关 SOP 和故障手册
7. 综合设备状态、历史告警和知识库内容生成故障分析
8. 输出处理建议
9. 根据严重程度判断是否创建工单
```

---

### 5.2 用户问答流程

```text
1. 用户输入设备运维问题
2. 智能体识别问题意图
3. 判断是否需要调用工具
4. 调用设备状态查询 / 历史告警查询 / 知识库检索工具
5. 结合检索结果生成回答
6. 返回引用来源和处理建议
```

---

## 6. 项目目录

```text
Kita-AIoT/
├── app/
│   ├── api/                    # FastAPI 路由
│   │   ├── devices.py           # 设备接口
│   │   ├── alarms.py            # 告警接口
│   │   ├── work_orders.py       # 工单接口
│   │   └── tools.py             # Agent 工具接口
│   ├── core/                   # 核心配置
│   │   ├── config.py
│   │   └── database.py
│   ├── models/                 # 数据模型
│   │   ├── device.py
│   │   ├── alarm.py
│   │   └── work_order.py
│   ├── services/               # 业务服务
│   │   ├── device_service.py
│   │   ├── alarm_service.py
│   │   ├── work_order_service.py
│   │   └── knowledge_service.py
│   ├── mqtt/                   # MQTT 消息处理
│   │   ├── subscriber.py
│   │   └── simulator.py
│   └── main.py
├── docs/
│   ├── prompts/                # Prompt 模板
│   ├── knowledge_base/          # 模拟知识库文档
│   └── workflow/                # Dify / 阿里百炼工作流说明
├── scripts/
│   ├── init_db.sql
│   └── mock_data.py
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 7. 数据模型设计

### 7.1 设备表

| 字段            | 说明     |
| ------------- | ------ |
| id            | 设备 ID  |
| name          | 设备名称   |
| type          | 设备类型   |
| status        | 在线状态   |
| location      | 部署位置   |
| battery_level | 电量     |
| temperature   | 温度     |
| last_seen_at  | 最近在线时间 |

---

### 7.2 告警表

| 字段          | 说明         |
| ----------- | ---------- |
| id          | 告警 ID      |
| device_id   | 设备 ID      |
| alarm_type  | 告警类型       |
| level       | 告警等级       |
| message     | 告警内容       |
| raw_payload | 原始 MQTT 消息 |
| created_at  | 告警时间       |

---

### 7.3 工单表

| 字段         | 说明    |
| ---------- | ----- |
| id         | 工单 ID |
| device_id  | 设备 ID |
| alarm_id   | 告警 ID |
| title      | 工单标题  |
| reason     | 故障原因  |
| suggestion | 处理建议  |
| status     | 工单状态  |
| created_at | 创建时间  |

---

## 8. API 示例

### 8.1 查询设备状态

```http
GET /api/v1/devices/{device_id}/status
```

响应示例：

```json
{
  "device_id": "device-001",
  "status": "online",
  "battery_level": 78,
  "temperature": 42.5,
  "last_seen_at": "2026-06-23 10:30:00"
}
```

---

### 8.2 查询历史告警

```http
GET /api/v1/devices/{device_id}/alarms
```

响应示例：

```json
{
  "device_id": "device-001",
  "alarms": [
    {
      "alarm_type": "temperature_high",
      "level": "warning",
      "message": "设备温度超过阈值",
      "created_at": "2026-06-23 10:20:00"
    }
  ]
}
```

---

### 8.3 创建工单

```http
POST /api/v1/work-orders
```

请求示例：

```json
{
  "device_id": "device-001",
  "alarm_id": "alarm-001",
  "title": "设备温度过高告警处理",
  "reason": "设备连续上报温度过高，可能存在散热异常或环境温度过高问题",
  "suggestion": "建议检查设备散热口、风扇状态和部署环境温度"
}
```

响应示例：

```json
{
  "work_order_id": "wo-001",
  "status": "created"
}
```

---

### 8.4 Agent 工具接口

```http
POST /api/v1/tools/device-diagnosis
```

请求示例：

```json
{
  "device_id": "device-001",
  "question": "设备持续温度过高，应该如何处理？"
}
```

响应示例：

```json
{
  "device_id": "device-001",
  "analysis": "设备当前温度较高，结合历史告警判断，可能与散热异常有关。",
  "suggestion": [
    "检查设备散热口是否堵塞",
    "检查风扇是否正常运行",
    "确认设备部署环境温度是否过高",
    "如温度持续升高，应安排现场检修"
  ],
  "references": [
    {
      "title": "设备运维 SOP",
      "section": "温度异常处理流程"
    }
  ]
}
```

---

## 9. MQTT 告警消息示例

Topic：

```text
aiot/device/alarm
```

Payload：

```json
{
  "device_id": "device-001",
  "alarm_type": "temperature_high",
  "level": "warning",
  "message": "设备温度超过阈值",
  "temperature": 82.6,
  "timestamp": "2026-06-23 10:20:00"
}
```

---

## 10. Prompt 示例

### 10.1 故障诊断 Prompt

```text
你是一个 AIoT 设备运维智能体，请根据设备状态、历史告警和知识库检索结果进行故障分析。

请按照以下格式输出：

1. 告警概述
2. 可能原因
3. 排查步骤
4. 处理建议
5. 是否建议创建工单
6. 引用依据

要求：
- 不要编造知识库中不存在的设备参数；
- 如果信息不足，请明确说明需要补充哪些信息；
- 优先引用设备说明书、故障排查手册和运维 SOP；
- 输出应简洁、结构化，便于运维人员执行。
```

---

### 10.2 工单生成 Prompt

```text
请根据设备告警、故障分析结果和处理建议生成一条运维工单。

工单需要包含：
- 工单标题
- 设备编号
- 告警等级
- 故障原因
- 建议处理步骤
- 优先级
- 是否需要现场处理

要求：
- 标题简洁明确；
- 优先级根据告警等级和影响范围判断；
- 处理步骤应可执行；
- 不要输出与告警无关的内容。
```

---

## 11. 快速启动

### 11.1 克隆项目

```bash
git clone https://github.com/209044528/Kita-AIoT.git
cd Kita-AIoT
```

---

### 11.2 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

`.env` 示例：

```env
APP_NAME=Kita-AIoT
APP_ENV=dev

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kita_aiot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_HOST=localhost
REDIS_PORT=6379

MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=aiot/device/alarm

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

DIFY_API_BASE_URL=
DIFY_API_KEY=

BAILIAN_API_KEY=
```

---

### 11.3 Docker Compose 启动依赖

```bash
docker compose up -d
```

---

### 11.4 安装 Python 依赖

```bash
pip install -r requirements.txt
```

---

### 11.5 启动后端服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

接口文档：

```text
http://localhost:8000/docs
```

---

### 11.6 模拟设备告警

```bash
python app/mqtt/simulator.py
```

---

## 12. Dify / 阿里百炼工作流配置

### 12.1 知识库配置

建议上传以下模拟文档：

```text
docs/knowledge_base/
├── device_manual.md
├── troubleshooting_guide.md
├── maintenance_sop.md
├── alarm_faq.md
└── historical_work_orders.md
```

知识库配置建议：

| 配置项    | 建议值          |
| ------ | ------------ |
| 切分方式   | 自动切分 / 按标题切分 |
| Top K  | 3～5          |
| 相似度阈值  | 0.4～0.6      |
| 是否返回引用 | 是            |
| 是否开启重排 | 根据平台能力开启     |

---

### 12.2 工具接口配置

在 Dify / 阿里百炼中配置以下 HTTP 工具：

| 工具名称              | Method | URL                                  |
| ----------------- | ------ | ------------------------------------ |
| get_device_status | GET    | `/api/v1/devices/{device_id}/status` |
| get_recent_alarms | GET    | `/api/v1/devices/{device_id}/alarms` |
| create_work_order | POST   | `/api/v1/work-orders`                |
| device_diagnosis  | POST   | `/api/v1/tools/device-diagnosis`     |

---

### 12.3 工作流节点示例

```text
开始节点
  → 用户问题 / 告警输入
  → 意图识别节点
  → 设备状态查询工具
  → 历史告警查询工具
  → 知识库检索节点
  → 故障诊断 LLM 节点
  → 是否创建工单判断节点
  → 工单创建工具
  → 输出处理建议
```

---

## 13. 项目亮点

* 将 AI Agent、RAG 知识库和 AIoT 告警处理场景结合，模拟企业设备运维闭环；
* 使用 FastAPI 将设备查询、告警查询、工单创建等能力封装为可被智能体调用的工具；
* 通过 MQTT 模拟设备实时告警上报，贴近物联网设备接入场景；
* 通过 Dify / 阿里百炼搭建智能体工作流，降低 Agent 应用开发和调试成本；
* 使用知识库检索和引用来源返回，提升故障分析结果的可信度；
* 针对故障诊断、知识问答、工单生成等场景设计 Prompt 模板，提升输出结构化程度。

---

## 14. 后续规划

* 支持更多设备类型和告警类型；
* 接入真实 MQTT Broker 与设备数据源；
* 增加工单状态流转和处理记录；
* 增加工作流执行日志与 Agent 调用链路追踪；
* 支持多知识库和多租户隔离；
* 接入前端管理页面，展示设备、告警、工单和智能体分析结果；
* 对比 Dify、阿里百炼、n8n 在 AIoT 工作流中的适用场景。

---

## 15. 适用场景

本项目适用于以下场景的 Demo 或学习参考：

* AI Agent 应用开发；
* 企业知识库 RAG；
* AIoT 设备运维；
* 智能客服 / 智能工单；
* 大模型工作流编排；
* FastAPI 工具服务封装；
* MQTT 设备消息接入。