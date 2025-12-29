这份架构设计旨在为 **米特（Mint）** 打造一个具备“具身智能”的神经中枢。


---

# 🤖 米特（Mint）具身智能后端架构设计方案

## 1. 系统总体架构 (System Overview)

米特采用 **“分布式感知 + 集中式决策”** 的架构。Python 后端作为“中枢大脑”，连接 AI 云端逻辑与本地物理硬件。

### 三层架构模型：

* **感知层 (Perception Layer)**：USB 摄像头（视觉）、ESP32 麦克风（听觉）、CMC/Tavily API（数据觉）。
* **决策层 (Decision Layer)**：Python 后端逻辑 + Dify Agent（DeepSeek-V3 推理）。
* **执行层 (Action Layer)**：TTS 语音（火山引擎）、ESP32-C3（眼睛/灯效）、舵机（肢体动作）。

---

## 2. 核心功能模块 (Functional Modules)

### A. 硬件通信模块 (Hardware Comm Hub)

* **WebSocket Server**：维持与主 ESP32 的全双工长连接，负责音频流传输与舵机指令下发。
* **Serial Manager**：通过 USB 转串口连接 ESP32-C3，负责发送极其简洁的表情代码（如 `FACE:01`）。
* **USB Camera Stream**：利用 OpenCV 开启独立线程，实时捕捉画面并支持人脸检测。

### B. AI 编排模块 (AI Orchestrator)

* **Dify API Client**：封装 Dify 的 Chatflow 接口，支持上下文记忆、工具调用（CMC/Tavily）。
* **JSON Parser**：核心插件，专门负责从 Dify 的回复文本中利用正则表达式提取 `{"action": "..."}` 代码块。
* **TTS Integration**：将解析后的文本实时送入火山引擎流式接口，并将生成的音频二进制流分片推送到 WebSocket。

### C. 视觉情报模块 (Vision Intelligence)

* **Vision Buffer**：当用户触发“看图”指令时，截取当前摄像头帧并压缩为 Base64。
* **RWA Dashboard (Thread)**：独立线程监控 CMC API。若关注的代币（如 ONDO）波动超过阈值，主动中断当前逻辑并触发预警动作。

---

## 3. 核心数据流控制 (Data Flow)

1. **输入触发**：用户说话  ESP32 采集音频  WebSocket  后端。
2. **语义解析**：后端调用 Dify  Agent 调用 Tavily/CMC  返回带动作的回复。
3. **多路分发**：
* **音频路**：回复文字  火山引擎 TTS  音频流回传给 ESP32。
* **表情路**：解析 Action  Serial 指令  ESP32-C3 切换屏幕动画。
* **动作路**：解析 Action  WebSocket 指令  主 ESP32 驱动舵机。



---

## 4. 详细执行路线图 (Implementation Roadmap)

### 第一阶段：中枢搭建 (The Core)

* [ ] 编写 `main.py` 启动异步 WebSocket 服务器。
* [ ] 接入 Dify SDK，确保能发送 query 并接收到包含 JSON 动作的回复。
* [ ] 接入火山引擎 TTS，实现文字转语音播放。

### 第二阶段：动作同步 (Physical Sync)

* [ ] 编写 `HardwareBridge` 类，实现动作指令到舵机角度和表情代码的映射。
* [ ] 编写串口监听逻辑，确保 Python 能与副 ESP32-C3 稳定通信。

### 第三阶段：视觉与 Web3 增强 (Intelligence Up)

* [ ] 集成 OpenCV 窗口，实现“米特的第一视角”。
* [ ] 编写 CMC 轮询脚本，实现 Web3 市场异动时的 LED 颜色预警（如：大涨闪绿光，大跌闪红光）。

---
