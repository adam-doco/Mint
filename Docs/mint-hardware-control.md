# 米特(Mint) 硬件控制模块文档

本文档详细说明了米特智能助手的所有硬件控制功能，包括舵机动作、表情控制、LED 灯效、音量控制、屏幕控制和音乐播放等。

---

## 目录

1. [概述](#概述)
2. [系统架构](#系统架构)
3. [可用工具列表](#可用工具列表)
4. [硬件控制工具详细说明](#硬件控制工具详细说明)
   - [mint_motion - 舵机动作控制](#mint_motion---舵机动作控制)
   - [mint_emotion - 表情控制](#mint_emotion---表情控制)
   - [mint_led - LED 灯效控制](#mint_led---led-灯效控制)
   - [mint_led_color - 自定义 LED 颜色](#mint_led_color---自定义-led-颜色)
   - [mint_volume - 音量控制](#mint_volume---音量控制)
   - [mint_get_volume - 查询音量](#mint_get_volume---查询音量)
   - [mint_brightness - 屏幕亮度控制](#mint_brightness---屏幕亮度控制)
   - [mint_screen_power - 屏幕开关控制](#mint_screen_power---屏幕开关控制)
5. [系统控制工具详细说明](#系统控制工具详细说明)
   - [play_music - 音乐播放](#play_music---音乐播放)
   - [handle_exit_intent - 退出对话](#handle_exit_intent---退出对话)
6. [Dify 配置指南](#dify-配置指南)
7. [使用示例](#使用示例)
8. [故障排除](#故障排除)

---

## 概述

米特硬件控制模块允许 AI 通过 Function Calling 机制控制物理硬件，实现更加生动的人机交互体验。

### 支持的硬件

| 硬件 | 控制方式 | 功能 |
|------|---------|------|
| 舵机（2轴云台） | WebSocket → ESP32 主控 | 头部动作（点头、摇头、转向等） |
| LED 眼睛显示屏 | 串口 → ESP32-C3 副控 | 表情显示（开心、难过等） |
| RGB LED 灯带 | 串口 → ESP32-C3 副控 | 灯光效果（呼吸、彩虹等） |
| 扬声器 | WebSocket → ESP32 主控 | 音量调节、静音控制 |
| 屏幕 | WebSocket → ESP32 主控 | 亮度调节、开关控制 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         服务器端                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   Dify LLM  │───→│ 硬件控制插件  │───→│ HardwareBridge│  │
│  │ (Function   │    │ mint_motion  │    │               │  │
│  │  Calling)   │    │ mint_emotion │    │ - WebSocket   │  │
│  │             │    │ mint_led     │    │ - Serial      │  │
│  │             │    │ mint_volume  │    │               │  │
│  │             │    │ play_music   │    │               │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket │ 串口
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        硬件端                                │
│  ┌────────────────┐              ┌────────────────────┐     │
│  │   ESP32 主控   │───串口连接───→│   ESP32-C3 副控    │     │
│  │                │              │                    │     │
│  │  - WebSocket   │              │  - 表情显示        │     │
│  │  - 舵机控制    │              │  - LED 控制        │     │
│  │  - 音量控制    │              │                    │     │
│  │  - 音频播放    │              │                    │     │
│  └────────────────┘              └────────────────────┘     │
│         │                                  │                │
│         ↓                                  ↓                │
│  ┌────────────┐                    ┌────────────────┐      │
│  │ 2轴舵机    │                    │ LED眼睛 + 灯带 │       │
│  │ 扬声器     │                    │                │       │
│  └────────────┘                    └────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 可用工具列表

### 硬件控制类（8个）

| 工具名称 | 功能 | 类型 |
|---------|------|------|
| `mint_motion` | 控制头部舵机动作 | IOT_CTL |
| `mint_emotion` | 控制眼睛表情显示 | IOT_CTL |
| `mint_led` | 设置预设 LED 灯效 | IOT_CTL |
| `mint_led_color` | 设置自定义 LED 颜色 | IOT_CTL |
| `mint_volume` | 控制音量大小 | IOT_CTL |
| `mint_get_volume` | 查询当前音量 | IOT_CTL |
| `mint_brightness` | 控制屏幕亮度 | IOT_CTL |
| `mint_screen_power` | 控制屏幕开关 | IOT_CTL |

### 系统控制类（2个）

| 工具名称 | 功能 | 类型 |
|---------|------|------|
| `play_music` | 播放本地音乐 | SYSTEM_CTL |
| `handle_exit_intent` | 退出对话 | SYSTEM_CTL |

---

## 硬件控制工具详细说明

### mint_motion - 舵机动作控制

控制米特的头部动作，包括点头、摇头、歪头、看向不同方向等。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `motion` | string | 是 | - | 动作类型 |
| `speed` | string | 否 | `normal` | 动作速度 |

#### motion 可选值

| 值 | 中文名称 | 说明 |
|---|---------|------|
| `neutral` | 回正 | 头部回到中立位置 |
| `nod` | 点头 | 上下点头表示肯定 |
| `shake` | 摇头 | 左右摇头表示否定 |
| `tilt_left` | 左歪头 | 头向左倾斜，表示好奇或疑惑 |
| `tilt_right` | 右歪头 | 头向右倾斜，表示好奇或疑惑 |
| `look_up` | 抬头 | 头部向上抬起 |
| `look_down` | 低头 | 头部向下低垂 |
| `look_left` | 向左看 | 头部转向左侧 |
| `look_right` | 向右看 | 头部转向右侧 |
| `excited` | 兴奋 | 快速抖动表示兴奋 |
| `shy` | 害羞 | 头部低垂并偏向一侧 |
| `greeting` | 打招呼 | 组合动作，点头 + 左右转动 |

#### speed 可选值

| 值 | 说明 |
|---|------|
| `slow` | 慢速（1.5倍时间） |
| `normal` | 正常速度 |
| `fast` | 快速（0.6倍时间） |

#### Dify 工具配置

```json
{
  "name": "mint_motion",
  "description": "控制米特的头部动作。可以让米特点头、摇头、歪头、抬头、低头、向左右看等。当用户要求米特做动作，或者在对话中需要配合肢体语言时使用。例如：'点点头'、'摇摇头'、'看看我'、'打个招呼'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "motion": {
        "type": "string",
        "description": "动作类型：neutral(回正)、nod(点头)、shake(摇头)、tilt_left(左歪头)、tilt_right(右歪头)、look_up(抬头)、look_down(低头)、look_left(向左看)、look_right(向右看)、excited(兴奋)、shy(害羞)、greeting(打招呼)",
        "enum": ["neutral", "nod", "shake", "tilt_left", "tilt_right", "look_up", "look_down", "look_left", "look_right", "excited", "shy", "greeting"]
      },
      "speed": {
        "type": "string",
        "description": "动作速度：slow(慢速)、normal(正常)、fast(快速)",
        "enum": ["slow", "normal", "fast"]
      }
    },
    "required": ["motion"]
  }
}
```

---

### mint_emotion - 表情控制

控制米特的眼睛表情，让米特能够表达各种情感。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `emotion` | string | 是 | - | 表情类型 |

#### emotion 可选值

| 值 | 中文名称 | 说明 |
|---|---------|------|
| `neutral` | 正常 | 默认表情，眼睛正常大小 |
| `happy` | 开心 | 弯弯的眼睛，表示高兴 |
| `sad` | 难过 | 眼睛下垂，眉毛下弯 |
| `angry` | 生气 | 眼睛变小，眉毛上扬 |
| `surprised` | 惊讶 | 眼睛睁大，瞳孔放大 |
| `sleepy` | 困倦 | 眼睛半闭，表示困倦 |
| `thinking` | 思考 | 眼睛看向一侧，表示思考 |
| `love` | 爱心 | 眼睛变成爱心形状 |
| `doubt` | 怀疑 | 一只眼睛眯起，表示怀疑 |
| `scared` | 害怕 | 瞳孔缩小，表示害怕 |
| `proud` | 得意 | 弯眼 + 眼睛上扬 |
| `speechless` | 无语 | 眼睛变成一条线 |

#### Dify 工具配置

```json
{
  "name": "mint_emotion",
  "description": "控制米特的眼睛表情。可以让米特显示开心、难过、生气、惊讶等各种表情。当对话中需要表达情感时使用，例如用户说了有趣的事就显示开心，用户说了难过的事就显示难过。也可以响应用户直接要求改变表情。",
  "parameters": {
    "type": "object",
    "properties": {
      "emotion": {
        "type": "string",
        "description": "表情类型：neutral(正常)、happy(开心)、sad(难过)、angry(生气)、surprised(惊讶)、sleepy(困倦)、thinking(思考)、love(爱心)、doubt(怀疑)、scared(害怕)、proud(得意)、speechless(无语)",
        "enum": ["neutral", "happy", "sad", "angry", "surprised", "sleepy", "thinking", "love", "doubt", "scared", "proud", "speechless"]
      }
    },
    "required": ["emotion"]
  }
}
```

---

### mint_led - LED 灯效控制

控制米特的 LED 灯效，支持多种预设灯效。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `effect` | string | 是 | - | 灯效名称 |

#### effect 可选值

| 值 | 中文名称 | 说明 |
|---|---------|------|
| `off` | 关闭 | 关闭所有 LED 灯 |
| **呼吸灯效** | | |
| `breathing_white` | 白色呼吸 | 白色呼吸灯效果 |
| `breathing_cyan` | 青色呼吸 | 青色呼吸灯效果（默认待机灯效） |
| `breathing_blue` | 蓝色呼吸 | 蓝色呼吸灯效果 |
| `breathing_pink` | 粉色呼吸 | 粉色呼吸灯效果 |
| `breathing_green` | 绿色呼吸 | 绿色呼吸灯效果 |
| `breathing_orange` | 橙色呼吸 | 橙色呼吸灯效果 |
| **脉冲灯效** | | |
| `pulse_blue` | 蓝色脉冲 | 蓝色快速脉冲 |
| `pulse_green` | 绿色脉冲 | 绿色快速脉冲 |
| `pulse_red` | 红色脉冲 | 红色快速脉冲 |
| **特效** | | |
| `rainbow` | 彩虹 | 彩虹渐变效果 |
| `spin_purple` | 紫色旋转 | 紫色旋转追逐效果 |
| `spin_cyan` | 青色旋转 | 青色旋转追逐效果 |
| **闪烁** | | |
| `blink_yellow` | 黄色闪烁 | 黄色闪烁警示 |
| `blink_red` | 红色闪烁 | 红色闪烁警示 |
| **常亮** | | |
| `solid_white` | 白色常亮 | 白色持续亮起 |
| `solid_cyan` | 青色常亮 | 青色持续亮起 |

#### Dify 工具配置

```json
{
  "name": "mint_led",
  "description": "控制米特的 LED 灯光效果。可以设置不同颜色的呼吸灯、脉冲、彩虹、旋转、闪烁等效果。当用户要求改变灯光、营造氛围、或者需要视觉反馈时使用。例如：'把灯变成蓝色'、'开彩虹灯'、'关灯'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "effect": {
        "type": "string",
        "description": "灯效名称：off(关闭)、breathing_white(白色呼吸)、breathing_cyan(青色呼吸)、breathing_blue(蓝色呼吸)、breathing_pink(粉色呼吸)、breathing_green(绿色呼吸)、breathing_orange(橙色呼吸)、pulse_blue(蓝色脉冲)、pulse_green(绿色脉冲)、pulse_red(红色脉冲)、rainbow(彩虹)、spin_purple(紫色旋转)、spin_cyan(青色旋转)、blink_yellow(黄色闪烁)、blink_red(红色闪烁)、solid_white(白色常亮)、solid_cyan(青色常亮)",
        "enum": ["off", "breathing_white", "breathing_cyan", "breathing_blue", "breathing_pink", "breathing_green", "breathing_orange", "pulse_blue", "pulse_green", "pulse_red", "rainbow", "spin_purple", "spin_cyan", "blink_yellow", "blink_red", "solid_white", "solid_cyan"]
      }
    },
    "required": ["effect"]
  }
}
```

---

### mint_led_color - 自定义 LED 颜色

设置自定义的 RGB 颜色值，适用于预设灯效无法满足的情况。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `r` | integer | 是 | - | 红色分量 (0-255) |
| `g` | integer | 是 | - | 绿色分量 (0-255) |
| `b` | integer | 是 | - | 蓝色分量 (0-255) |
| `mode` | string | 否 | `breathing` | 灯光模式 |

#### mode 可选值

| 值 | 说明 |
|---|------|
| `solid` | 常亮模式 |
| `breathing` | 呼吸模式 |
| `pulse` | 脉冲模式 |

#### Dify 工具配置

```json
{
  "name": "mint_led_color",
  "description": "设置米特 LED 的自定义颜色。可以指定 RGB 值来设置任意颜色。当用户要求特定颜色但预设灯效中没有时使用。例如：'把灯变成紫色'、'我想要暖黄色的灯'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "r": {
        "type": "integer",
        "description": "红色分量，范围 0-255",
        "minimum": 0,
        "maximum": 255
      },
      "g": {
        "type": "integer",
        "description": "绿色分量，范围 0-255",
        "minimum": 0,
        "maximum": 255
      },
      "b": {
        "type": "integer",
        "description": "蓝色分量，范围 0-255",
        "minimum": 0,
        "maximum": 255
      },
      "mode": {
        "type": "string",
        "description": "灯光模式：solid(常亮)、breathing(呼吸)、pulse(脉冲)",
        "enum": ["solid", "breathing", "pulse"]
      }
    },
    "required": ["r", "g", "b"]
  }
}
```

---

### mint_volume - 音量控制

控制米特的音量大小，支持设置具体值或调大调小。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `action` | string | 是 | - | 音量操作类型 |
| `value` | integer | 否 | 50 | 音量值(0-100)，仅当 action 为 set 时需要 |

#### action 可选值

| 值 | 说明 |
|---|------|
| `set` | 设置具体音量值 |
| `up` | 调大音量 |
| `down` | 调小音量 |
| `mute` | 静音 |
| `unmute` | 取消静音 |

#### Dify 工具配置

```json
{
  "name": "mint_volume",
  "description": "控制米特的音量大小。可以设置具体音量值，或者调大、调小音量。当用户要求调整音量时使用，例如：'把音量调大一点'、'音量调到50'、'声音太大了'、'静音'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "音量操作类型：set(设置具体值)、up(调大)、down(调小)、mute(静音)、unmute(取消静音)",
        "enum": ["set", "up", "down", "mute", "unmute"]
      },
      "value": {
        "type": "integer",
        "description": "音量值(0-100)，仅当action为set时需要",
        "minimum": 0,
        "maximum": 100
      }
    },
    "required": ["action"]
  }
}
```

---

### mint_get_volume - 查询音量

查询米特当前的音量大小。

#### Dify 工具配置

```json
{
  "name": "mint_get_volume",
  "description": "查询米特当前的音量大小。当用户询问当前音量时使用，例如：'现在音量是多少？'、'音量多大？'等。",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

---

### mint_brightness - 屏幕亮度控制

控制米特屏幕（眼睛显示屏）的亮度。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `action` | string | 是 | - | 亮度操作类型 |
| `value` | integer | 否 | 80 | 亮度值(0-100)，仅当 action 为 set 时需要 |

#### action 可选值

| 值 | 说明 |
|---|------|
| `set` | 设置具体亮度值 |
| `up` | 调亮 |
| `down` | 调暗 |

#### Dify 工具配置

```json
{
  "name": "mint_brightness",
  "description": "控制米特屏幕（眼睛）的亮度。可以设置具体亮度值，或者调亮、调暗。当用户要求调整屏幕亮度时使用，例如：'屏幕太亮了'、'把亮度调低一点'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "亮度操作类型：set(设置具体值)、up(调亮)、down(调暗)",
        "enum": ["set", "up", "down"]
      },
      "value": {
        "type": "integer",
        "description": "亮度值(0-100)，仅当action为set时需要",
        "minimum": 0,
        "maximum": 100
      }
    },
    "required": ["action"]
  }
}
```

---

### mint_screen_power - 屏幕开关控制

控制米特屏幕（眼睛显示屏）的开关。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `power` | string | 是 | - | 开关状态 |

#### power 可选值

| 值 | 说明 |
|---|------|
| `on` | 打开屏幕 |
| `off` | 关闭屏幕 |

#### Dify 工具配置

```json
{
  "name": "mint_screen_power",
  "description": "控制米特屏幕（眼睛）的开关。当用户要求关闭或打开屏幕时使用，例如：'关闭屏幕'、'打开屏幕'、'闭上眼睛'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "power": {
        "type": "string",
        "description": "开关状态：on(打开)、off(关闭)",
        "enum": ["on", "off"]
      }
    },
    "required": ["power"]
  }
}
```

---

## 系统控制工具详细说明

### play_music - 音乐播放

播放本地音乐文件。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `song_name` | string | 是 | - | 歌曲名称或 "random" 随机播放 |

#### 说明

- 音乐文件存放在服务器的 `./music` 目录下
- 支持 `.mp3`、`.wav`、`.p3` 格式
- 如果指定歌名，会模糊匹配最相似的歌曲
- 如果传入 "random"，则随机播放一首

#### Dify 工具配置

```json
{
  "name": "play_music",
  "description": "唱歌、听歌、播放音乐的方法。当用户想听音乐时调用。",
  "parameters": {
    "type": "object",
    "properties": {
      "song_name": {
        "type": "string",
        "description": "歌曲名称，如果用户没有指定具体歌名则为'random'。示例：用户说'播放两只老虎'则传入'两只老虎'；用户说'播放音乐'则传入'random'"
      }
    },
    "required": ["song_name"]
  }
}
```

---

### handle_exit_intent - 退出对话

处理用户结束对话的意图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `say_goodbye` | string | 是 | - | 和用户友好结束对话的告别语 |

#### Dify 工具配置

```json
{
  "name": "handle_exit_intent",
  "description": "当用户想结束对话或需要退出系统时调用。例如用户说'再见'、'拜拜'、'我要走了'等。",
  "parameters": {
    "type": "object",
    "properties": {
      "say_goodbye": {
        "type": "string",
        "description": "和用户友好结束对话的告别语"
      }
    },
    "required": ["say_goodbye"]
  }
}
```

---

## Dify 配置指南

### 方法一：使用 OpenAPI Schema（推荐）

如果你想使用 Dify 的自定义工具（Custom Tools）功能，可以直接导入 OpenAPI Schema。

#### API 服务器地址

```
http://120.26.38.27:8003
```

#### OpenAPI Schema 文件

- YAML 格式：`Docs/mint-openapi-schema.yaml`
- JSON 格式：`Docs/mint-openapi-schema.json`

#### 配置步骤

1. 登录 Dify 控制台
2. 进入「工具」→「自定义工具」→「创建自定义工具」
3. 将 `mint-openapi-schema.json` 的内容复制粘贴到 Schema 输入框
4. 保存后即可在应用中使用这些工具

#### 可用 API 端点

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/v1/devices` | GET | 获取已连接设备列表 |
| `/api/v1/volume` | POST | 控制音量 |
| `/api/v1/brightness` | POST | 控制屏幕亮度 |
| `/api/v1/screen/power` | POST | 控制屏幕开关 |
| `/api/v1/motion` | POST | 控制舵机动作 |
| `/api/v1/emotion` | POST | 控制表情 |
| `/api/v1/led` | POST | 控制 LED 灯效 |
| `/api/v1/led/color` | POST | 设置自定义 LED 颜色 |

#### API 鉴权配置

所有 API 请求都需要进行鉴权，防止未授权访问。

##### 服务器端配置

在服务器的 `config.yaml` 或 `data/.config.yaml` 中添加以下配置：

```yaml
# 硬件控制 API 配置
hardware_api:
  # 是否启用鉴权 (默认: true)
  enabled: true
  # API Key
  api_key: "mint-hardware-api-2025888999"
```

##### 当前配置

| 配置项 | 值 |
|-------|-----|
| API Key | `mint-hardware-api-2025888999` |
| 服务器地址 | `http://120.26.38.27:8003` |

##### 请求头格式

调用 API 时需要在请求头中添加 API Key（二选一）：

**方式一：Bearer Token**
```
Authorization: Bearer mint-hardware-api-2025888999
```

**方式二：X-API-Key**
```
X-API-Key: mint-hardware-api-2025888999
```

##### Dify 鉴权配置

在 Dify 创建自定义工具时，选择鉴权方式：
- 鉴权类型：`API Key`
- Header 名称：`X-API-Key`
- API Key 值：`mint-hardware-api-2025888999`

或者选择：
- 鉴权类型：`Bearer`
- Token：`mint-hardware-api-2025888999`

#### 重要说明

- 所有 POST 请求都需要在请求体中包含 `device_id` 参数来指定要控制的设备
- 所有请求都必须携带有效的 API Key，否则返回 401 未授权错误

---

### 方法二：使用 Function Calling

如果你使用 Dify 的 Agent 模式并配置本地 Function Calling，请按以下步骤操作。

#### 步骤 1：进入 Dify 应用设置

1. 登录 Dify 控制台
2. 选择你的米特应用
3. 进入「编排」或「构建」页面

#### 步骤 2：添加工具

在应用中添加以下 10 个工具（按上述 JSON 配置添加）：

#### 硬件控制工具（8个）
1. `mint_motion` - 舵机动作
2. `mint_emotion` - 表情控制
3. `mint_led` - LED 灯效
4. `mint_led_color` - 自定义颜色
5. `mint_volume` - 音量控制
6. `mint_get_volume` - 查询音量
7. `mint_brightness` - 屏幕亮度
8. `mint_screen_power` - 屏幕开关

#### 系统控制工具（2个）
9. `play_music` - 音乐播放
10. `handle_exit_intent` - 退出对话

### 步骤 3：配置系统提示词

建议在系统提示词中添加以下内容：

```
你是米特(Mint)，一个可爱的智能助手机器人。你有物理身体，可以做出动作、表情和灯光变化。

当与用户对话时，你应该：
1. 在表达肯定时点头(nod)，否定时摇头(shake)
2. 根据对话情感变化调整表情(emotion)
3. 在用户要求时改变灯光效果(led)
4. 在用户要求时调整音量(volume)
5. 主动配合语言内容做出相应动作，让对话更生动

可用的动作：点头、摇头、歪头、抬头、低头、左右看、打招呼、害羞、兴奋
可用的表情：正常、开心、难过、生气、惊讶、困倦、思考、爱心、怀疑、害怕、得意、无语
可用的灯效：各种颜色的呼吸灯、脉冲、彩虹、旋转、闪烁等
音量控制：可以调大、调小、静音、设置具体值
屏幕控制：可以调节亮度、开关屏幕
音乐播放：可以播放本地音乐
```

---

## 使用示例

### 示例 1：问候场景

**用户**：你好米特！

**AI 行为**：
1. 调用 `mint_motion(motion="greeting")` - 打招呼动作
2. 调用 `mint_emotion(emotion="happy")` - 开心表情
3. 语音回复："你好呀！见到你真开心！"

### 示例 2：音量控制场景

**用户**：声音太大了，调小一点

**AI 行为**：
1. 调用 `mint_volume(action="down")` - 调小音量
2. 语音回复："好的，音量已调小"

**用户**：把音量调到 30

**AI 行为**：
1. 调用 `mint_volume(action="set", value=30)` - 设置音量
2. 语音回复："好的，音量已调整到 30"

### 示例 3：灯光控制场景

**用户**：把灯变成彩虹色

**AI 行为**：
1. 调用 `mint_led(effect="rainbow")` - 彩虹灯效
2. 语音回复："好的，彩虹灯已经打开啦！"

### 示例 4：播放音乐场景

**用户**：播放两只老虎

**AI 行为**：
1. 调用 `play_music(song_name="两只老虎")` - 播放音乐
2. 语音回复："正在为您播放，《两只老虎》"
3. 开始播放音乐文件

### 示例 5：退出对话场景

**用户**：再见，我要睡觉了

**AI 行为**：
1. 调用 `mint_motion(motion="nod")` - 点头
2. 调用 `mint_emotion(emotion="sleepy")` - 困倦表情
3. 调用 `handle_exit_intent(say_goodbye="晚安，祝你做个好梦！")` - 退出
4. 语音回复："晚安，祝你做个好梦！"

---

## 故障排除

### 问题 1：硬件不响应

**可能原因**：
- ESP32 WebSocket 连接断开
- 串口连接未建立

**解决方案**：
1. 检查服务器日志是否有连接错误
2. 确认 ESP32 已正确连接到服务器
3. 重启服务和设备

### 问题 2：音量控制无效

**可能原因**：
- ESP32 未正确处理 IoT 命令

**解决方案**：
1. 检查 ESP32 固件是否支持音量 IoT 命令
2. 确认 WebSocket 连接正常
3. 查看服务器日志确认命令已发送

### 问题 3：Dify 未调用工具

**可能原因**：
- 工具配置错误
- 系统提示词未正确引导

**解决方案**：
1. 检查工具的 JSON 配置是否正确
2. 在系统提示词中明确说明何时使用这些工具

### 问题 4：API 返回 401 未授权

**可能原因**：
- 未配置 API Key
- API Key 配置错误
- 请求头格式不正确

**解决方案**：
1. 确认服务器 `data/.config.yaml` 中已配置正确的 `hardware_api.api_key`
2. 确认 Dify 中配置的 API Key 与服务器一致
3. 检查请求头格式：`Authorization: Bearer <api_key>` 或 `X-API-Key: <api_key>`
4. 重启服务使配置生效

### 问题 5：设备列表为空

**可能原因**：
- ESP32 设备未连接到服务器
- 设备连接后已断开

**解决方案**：
1. 检查 ESP32 是否正常运行并连接到 WebSocket 服务器
2. 查看服务器日志确认设备连接状态
3. 调用 `/api/v1/devices` 接口查看当前已连接设备

---

## 文件位置

### 插件文件（xiaozhi-esp32-server/main/xiaozhi-server/）

| 文件 | 路径 | 说明 |
|-----|------|------|
| 舵机插件 | `plugins_func/functions/mint_motion.py` | 舵机动作控制 |
| 表情插件 | `plugins_func/functions/mint_emotion.py` | 表情控制 |
| LED 插件 | `plugins_func/functions/mint_led.py` | LED 灯效控制 |
| 音量插件 | `plugins_func/functions/mint_volume.py` | 音量控制 |
| 屏幕插件 | `plugins_func/functions/mint_screen.py` | 屏幕亮度/开关控制 |
| 音乐插件 | `plugins_func/functions/play_music.py` | 音乐播放 |
| 退出插件 | `plugins_func/functions/handle_exit_intent.py` | 退出对话 |
| 硬件桥接 | `core/hardware/hardware_bridge.py` | 底层硬件通信 |
| 动作协议 | `core/hardware/action_protocol.py` | 动作/表情/灯效定义 |

### HTTP API 相关文件

| 文件 | 路径 | 说明 |
|-----|------|------|
| 连接注册表 | `core/connection_registry.py` | 全局设备连接管理 |
| 硬件 API | `core/api/hardware_handler.py` | HTTP API 处理器 |
| HTTP 服务器 | `core/http_server.py` | HTTP 路由配置 |
| 连接处理 | `core/connection.py` | WebSocket 连接处理（含注册逻辑） |

### 文档文件（Mint/Docs/）

| 文件 | 说明 |
|-----|------|
| `mint-hardware-control.md` | 本文档，硬件控制完整说明 |
| `mint-openapi-schema.yaml` | OpenAPI 3.0 规范（YAML 格式） |
| `mint-openapi-schema.json` | OpenAPI 3.0 规范（JSON 格式，供 Dify 使用） |

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|-----|------|---------|
| 2024-12-30 | v1.0 | 初始版本，支持舵机、表情、LED 控制 |
| 2024-12-30 | v1.1 | 新增音量控制、屏幕控制、音乐播放、退出对话功能 |
| 2024-12-30 | v1.2 | 新增 HTTP API 接口，支持 Dify OpenAPI 调用；添加 API Key 鉴权机制 |
