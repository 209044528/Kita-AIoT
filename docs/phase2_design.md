# Kita-AIoT 二阶段设计

## 目标

- Dify 完整承接告警分析 Workflow。
- 阿里云百炼完成 OpenAI 兼容接口基础接入。
- FastAPI 提供约 5 个 Agent 工具。
- PostgreSQL 持久化设备、告警、工单、调用日志和工作流执行记录。
- MQTT 告警自动触发工作流。
- MinIO 保存设备文档或图片。
- Web 页面展示设备、告警、工单和工作流状态。

## 总体架构

```mermaid
flowchart TB
    Device["AIoT 设备 / 模拟器"] -->|"MQTT 告警"| Broker["Mosquitto"]
    Broker --> Consumer["FastAPI MQTT Consumer"]
    Consumer --> Engine["告警工作流引擎"]

    User["运维人员"] --> Web["监控页面"]
    Web --> API["FastAPI Agent Tools"]
    Dify["Dify Workflow + RAG"] --> API
    Engine -->|"Workflow API"| Dify
    Bailian["阿里云百炼"] <-. "基础连通" .-> API

    API --> PostgreSQL[("PostgreSQL")]
    Engine --> PostgreSQL
    API --> MinIO[("MinIO 文档/图片")]
    Dify --> KB["Dify 知识库"]
```

## 数据模型

```mermaid
erDiagram
    DEVICES ||--o{ ALARMS : generates
    DEVICES ||--o{ WORK_ORDERS : owns
    ALARMS o|--o{ WORK_ORDERS : creates
    DEVICES ||--o{ DOCUMENTS : has

    DEVICES {
        string device_id PK
        string name
        string type
        string status
        float temperature
        int battery_level
        datetime last_seen_at
    }
    ALARMS {
        string alarm_id PK
        string device_id FK
        string alarm_type
        string level
        json raw_payload
        datetime created_at
    }
    WORK_ORDERS {
        string work_order_id PK
        string device_id FK
        string alarm_id FK
        string priority
        string status
    }
    CALL_LOGS {
        string call_id PK
        string request_id
        string method
        string path
        int status_code
        float duration_ms
    }
    WORKFLOW_EXECUTIONS {
        string execution_id PK
        string trigger_type
        string trigger_ref
        string platform
        string status
        json input_payload
        json output_payload
    }
    DOCUMENTS {
        string document_id PK
        string device_id FK
        string object_name
        string bucket
        int size
    }
```

## MQTT 工作流

```mermaid
sequenceDiagram
    participant Device as 设备/模拟器
    participant MQTT as Mosquitto
    participant API as FastAPI Consumer
    participant DB as PostgreSQL
    participant Dify as Dify Workflow

    Device->>MQTT: publish aiot/device/alarm
    MQTT->>API: alarm payload
    API->>DB: 创建 workflow_execution(running)
    API->>DB: 保存告警并更新设备
    API->>Dify: 调用 Workflow API
    Dify-->>API: 分析结果
    API->>DB: critical 时创建 P1 工单
    API->>DB: workflow_execution(succeeded/failed)
```

## 容错策略

- Dify 未配置时，使用本地规则诊断，保证本地演示链路可运行。
- 工作流异常写入 `workflow_executions.error_message`。
- HTTP 日志写入失败不会影响业务响应。
- MinIO 未启用时文档接口返回 503，并给出配置提示。
- 数据库连接使用 `pool_pre_ping` 检测失效连接。
