# 米特(Mint) ESP32 固件升级指南

本文档说明如何为米特硬件升级 ESP32 固件，添加 IoT 设备控制功能（舵机、LED、音量、屏幕等）。

---

## 目录

1. [概述](#概述)
2. [当前问题分析](#当前问题分析)
3. [需要添加的功能](#需要添加的功能)
4. [IoT 协议规范](#iot-协议规范)
5. [固件代码修改指南](#固件代码修改指南)
6. [服务器端命令格式](#服务器端命令格式)

---

## 概述

米特硬件基于 xiaozhi-esp32 开源项目，需要添加以下硬件控制功能：

| 硬件 | 控制方式 | 状态 |
|------|---------|------|
| 舵机（2轴云台） | PWM/I2C | 待添加 |
| LED 灯带 | WS2812/串口 | 待添加 |
| 音量 | 音频芯片 | 需确认 |
| 屏幕亮度 | PWM/I2C | 需确认 |

---

## 当前问题分析

### 问题现象
服务器通过 Dify 发送硬件控制命令，但 ESP32 没有响应。

### 根本原因
1. **固件未上报 IoT 描述符**：ESP32 连接时没有告诉服务器它支持哪些 IoT 设备
2. **固件未实现 IoT 命令处理**：即使收到命令也不知道如何处理
3. **缺少硬件驱动**：舵机、LED 等硬件没有对应的驱动代码

### 通信流程（应有的）

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│  Dify   │                    │ Server  │                    │  ESP32  │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │  1. 调用硬件控制 API          │                              │
     │ ─────────────────────────────>                              │
     │                              │                              │
     │                              │  2. 设备连接时上报描述符       │
     │                              │ <─────────────────────────────
     │                              │  {"type":"iot",              │
     │                              │   "descriptors":[...]}       │
     │                              │                              │
     │                              │  3. 发送 IoT 命令             │
     │                              │ ─────────────────────────────>
     │                              │  {"type":"iot",              │
     │                              │   "commands":[...]}          │
     │                              │                              │
     │                              │  4. 执行命令并更新状态         │
     │                              │ <─────────────────────────────
     │                              │  {"type":"iot",              │
     │  5. 返回执行结果              │   "states":[...]}            │
     │ <─────────────────────────────                              │
     │                              │                              │
```

---

## 需要添加的功能

### 1. IoT 描述符上报

ESP32 连接到服务器后，需要发送支持的设备列表：

```json
{
  "type": "iot",
  "descriptors": [
    {
      "name": "Speaker",
      "description": "扬声器",
      "properties": {
        "volume": {
          "description": "当前音量",
          "type": "number"
        }
      },
      "methods": {
        "SetVolume": {
          "description": "设置音量",
          "parameters": {
            "volume": {
              "description": "音量值(0-100)",
              "type": "number"
            }
          }
        },
        "VolumeUp": {
          "description": "调大音量"
        },
        "VolumeDown": {
          "description": "调小音量"
        }
      }
    },
    {
      "name": "Screen",
      "description": "屏幕",
      "properties": {
        "brightness": {
          "description": "当前亮度",
          "type": "number"
        }
      },
      "methods": {
        "SetBrightness": {
          "description": "设置亮度",
          "parameters": {
            "brightness": {
              "description": "亮度值(0-100)",
              "type": "number"
            }
          }
        },
        "TurnOn": {
          "description": "打开屏幕"
        },
        "TurnOff": {
          "description": "关闭屏幕"
        }
      }
    },
    {
      "name": "Servo",
      "description": "舵机云台",
      "properties": {
        "pan": {
          "description": "水平角度",
          "type": "number"
        },
        "tilt": {
          "description": "垂直角度",
          "type": "number"
        }
      },
      "methods": {
        "SetAngle": {
          "description": "设置角度",
          "parameters": {
            "pan": {
              "description": "水平角度(-90到90)",
              "type": "number"
            },
            "tilt": {
              "description": "垂直角度(-45到45)",
              "type": "number"
            }
          }
        },
        "ExecuteMotion": {
          "description": "执行预设动作",
          "parameters": {
            "motion": {
              "description": "动作名称",
              "type": "string"
            }
          }
        }
      }
    },
    {
      "name": "LED",
      "description": "LED灯带",
      "properties": {
        "effect": {
          "description": "当前灯效",
          "type": "string"
        }
      },
      "methods": {
        "SetEffect": {
          "description": "设置灯效",
          "parameters": {
            "effect": {
              "description": "灯效名称",
              "type": "string"
            }
          }
        },
        "SetColor": {
          "description": "设置颜色",
          "parameters": {
            "red": {
              "description": "红色(0-255)",
              "type": "number"
            },
            "green": {
              "description": "绿色(0-255)",
              "type": "number"
            },
            "blue": {
              "description": "蓝色(0-255)",
              "type": "number"
            }
          }
        }
      }
    }
  ]
}
```

### 2. IoT 命令处理

ESP32 需要监听并处理来自服务器的 IoT 命令：

```json
{
  "type": "iot",
  "commands": [
    {
      "name": "Speaker",
      "method": "SetVolume",
      "parameters": {
        "volume": 50
      }
    }
  ]
}
```

### 3. 状态更新上报

执行命令后，需要上报最新状态：

```json
{
  "type": "iot",
  "states": [
    {
      "name": "Speaker",
      "state": {
        "volume": 50
      }
    }
  ]
}
```

---

## IoT 协议规范

### 消息类型

| type | 方向 | 说明 |
|------|------|------|
| `iot` + `descriptors` | ESP32 → Server | 上报支持的设备列表 |
| `iot` + `commands` | Server → ESP32 | 发送控制命令 |
| `iot` + `states` | ESP32 → Server | 上报设备状态 |

### 设备名称规范

| 设备名 | 说明 |
|--------|------|
| `Speaker` | 扬声器/音量控制 |
| `Screen` | 屏幕/亮度控制 |
| `Servo` | 舵机云台 |
| `LED` | LED 灯带 |
| `Expression` | 表情显示 |

### 方法名称规范

| 设备 | 方法名 | 参数 | 说明 |
|------|--------|------|------|
| Speaker | SetVolume | volume: 0-100 | 设置音量 |
| Speaker | VolumeUp | - | 调大音量 |
| Speaker | VolumeDown | - | 调小音量 |
| Speaker | Mute | - | 静音 |
| Speaker | Unmute | - | 取消静音 |
| Screen | SetBrightness | brightness: 0-100 | 设置亮度 |
| Screen | TurnOn | - | 打开屏幕 |
| Screen | TurnOff | - | 关闭屏幕 |
| Servo | SetAngle | pan, tilt | 设置角度 |
| Servo | ExecuteMotion | motion: string | 执行预设动作 |
| LED | SetEffect | effect: string | 设置灯效 |
| LED | SetColor | red, green, blue | 设置颜色 |

### 预设动作列表 (Servo.ExecuteMotion)

| motion | 说明 |
|--------|------|
| neutral | 回正 |
| nod | 点头 |
| shake | 摇头 |
| tilt_left | 左歪头 |
| tilt_right | 右歪头 |
| look_up | 抬头 |
| look_down | 低头 |
| look_left | 向左看 |
| look_right | 向右看 |
| excited | 兴奋 |
| shy | 害羞 |
| greeting | 打招呼 |

### 预设灯效列表 (LED.SetEffect)

| effect | 说明 |
|--------|------|
| off | 关闭 |
| default | 默认白光 |
| rainbow | 彩虹 |
| breathing | 呼吸灯 |
| pulse | 脉冲 |

---

## 固件代码修改指南

### 文件结构建议

在 `xiaozhi-esp32/main/` 目录下创建以下文件：

```
main/
├── iot/
│   ├── iot_manager.h        # IoT 管理器头文件
│   ├── iot_manager.cc       # IoT 管理器实现
│   ├── iot_device.h         # IoT 设备基类
│   ├── speaker_device.cc    # 扬声器设备
│   ├── screen_device.cc     # 屏幕设备
│   ├── servo_device.cc      # 舵机设备
│   └── led_device.cc        # LED 设备
```

### 1. IoT 管理器 (iot_manager.h)

```cpp
#ifndef IOT_MANAGER_H
#define IOT_MANAGER_H

#include <string>
#include <vector>
#include <functional>
#include <cJSON.h>

class IotDevice;

class IotManager {
public:
    static IotManager& GetInstance();

    // 注册设备
    void RegisterDevice(IotDevice* device);

    // 生成描述符 JSON
    std::string GetDescriptorsJson();

    // 处理 IoT 命令
    void HandleCommand(const cJSON* command);

    // 获取所有设备状态
    std::string GetStatesJson();

private:
    std::vector<IotDevice*> devices_;
};

#endif
```

### 2. IoT 设备基类 (iot_device.h)

```cpp
#ifndef IOT_DEVICE_H
#define IOT_DEVICE_H

#include <string>
#include <cJSON.h>

class IotDevice {
public:
    virtual ~IotDevice() = default;

    // 获取设备名称
    virtual std::string GetName() = 0;

    // 获取设备描述
    virtual std::string GetDescription() = 0;

    // 生成设备描述符
    virtual cJSON* GetDescriptor() = 0;

    // 处理方法调用
    virtual bool HandleMethod(const std::string& method, const cJSON* params) = 0;

    // 获取当前状态
    virtual cJSON* GetState() = 0;
};

#endif
```

### 3. 扬声器设备示例 (speaker_device.cc)

```cpp
#include "iot_device.h"
#include "audio_codec.h"

class SpeakerDevice : public IotDevice {
public:
    std::string GetName() override { return "Speaker"; }
    std::string GetDescription() override { return "扬声器"; }

    cJSON* GetDescriptor() override {
        cJSON* desc = cJSON_CreateObject();
        cJSON_AddStringToObject(desc, "name", "Speaker");
        cJSON_AddStringToObject(desc, "description", "扬声器");

        // Properties
        cJSON* props = cJSON_CreateObject();
        cJSON* volume_prop = cJSON_CreateObject();
        cJSON_AddStringToObject(volume_prop, "description", "当前音量");
        cJSON_AddStringToObject(volume_prop, "type", "number");
        cJSON_AddItemToObject(props, "volume", volume_prop);
        cJSON_AddItemToObject(desc, "properties", props);

        // Methods
        cJSON* methods = cJSON_CreateObject();

        // SetVolume
        cJSON* set_volume = cJSON_CreateObject();
        cJSON_AddStringToObject(set_volume, "description", "设置音量");
        cJSON* sv_params = cJSON_CreateObject();
        cJSON* vol_param = cJSON_CreateObject();
        cJSON_AddStringToObject(vol_param, "description", "音量值(0-100)");
        cJSON_AddStringToObject(vol_param, "type", "number");
        cJSON_AddItemToObject(sv_params, "volume", vol_param);
        cJSON_AddItemToObject(set_volume, "parameters", sv_params);
        cJSON_AddItemToObject(methods, "SetVolume", set_volume);

        // VolumeUp
        cJSON* vol_up = cJSON_CreateObject();
        cJSON_AddStringToObject(vol_up, "description", "调大音量");
        cJSON_AddItemToObject(methods, "VolumeUp", vol_up);

        // VolumeDown
        cJSON* vol_down = cJSON_CreateObject();
        cJSON_AddStringToObject(vol_down, "description", "调小音量");
        cJSON_AddItemToObject(methods, "VolumeDown", vol_down);

        cJSON_AddItemToObject(desc, "methods", methods);

        return desc;
    }

    bool HandleMethod(const std::string& method, const cJSON* params) override {
        auto& board = Board::GetInstance();
        auto codec = board.GetAudioCodec();

        if (method == "SetVolume") {
            auto vol = cJSON_GetObjectItem(params, "volume");
            if (cJSON_IsNumber(vol)) {
                volume_ = vol->valueint;
                codec->SetOutputVolume(volume_);
                return true;
            }
        } else if (method == "VolumeUp") {
            volume_ = std::min(100, volume_ + 10);
            codec->SetOutputVolume(volume_);
            return true;
        } else if (method == "VolumeDown") {
            volume_ = std::max(0, volume_ - 10);
            codec->SetOutputVolume(volume_);
            return true;
        }
        return false;
    }

    cJSON* GetState() override {
        cJSON* state = cJSON_CreateObject();
        cJSON_AddStringToObject(state, "name", "Speaker");
        cJSON* state_obj = cJSON_CreateObject();
        cJSON_AddNumberToObject(state_obj, "volume", volume_);
        cJSON_AddItemToObject(state, "state", state_obj);
        return state;
    }

private:
    int volume_ = 70;
};
```

### 4. 在 WebSocket 协议中集成

修改 `websocket_protocol.cc`：

```cpp
// 在 OpenAudioChannel() 成功后发送 IoT 描述符
bool WebsocketProtocol::OpenAudioChannel() {
    // ... 现有代码 ...

    // 发送 IoT 描述符
    SendIotDescriptors();

    return true;
}

void WebsocketProtocol::SendIotDescriptors() {
    auto& iot = IotManager::GetInstance();
    std::string descriptors = iot.GetDescriptorsJson();
    SendText(descriptors);
}

// 在 OnData 回调中处理 IoT 命令
void WebsocketProtocol::HandleIncomingJson(const cJSON* root) {
    auto type = cJSON_GetObjectItem(root, "type");
    if (cJSON_IsString(type)) {
        if (strcmp(type->valuestring, "iot") == 0) {
            auto commands = cJSON_GetObjectItem(root, "commands");
            if (cJSON_IsArray(commands)) {
                HandleIotCommands(commands);
            }
        }
    }
}

void WebsocketProtocol::HandleIotCommands(const cJSON* commands) {
    auto& iot = IotManager::GetInstance();

    int size = cJSON_GetArraySize(commands);
    for (int i = 0; i < size; i++) {
        auto cmd = cJSON_GetArrayItem(commands, i);
        iot.HandleCommand(cmd);
    }

    // 发送更新后的状态
    std::string states = iot.GetStatesJson();
    SendText(states);
}
```

### 5. 舵机控制示例

```cpp
#include "driver/ledc.h"

class ServoDevice : public IotDevice {
public:
    ServoDevice(int pan_gpio, int tilt_gpio)
        : pan_gpio_(pan_gpio), tilt_gpio_(tilt_gpio) {
        InitPWM();
    }

    void InitPWM() {
        // 配置 LEDC 定时器
        ledc_timer_config_t timer_conf = {
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .duty_resolution = LEDC_TIMER_13_BIT,
            .timer_num = LEDC_TIMER_0,
            .freq_hz = 50,  // 舵机使用 50Hz
            .clk_cfg = LEDC_AUTO_CLK
        };
        ledc_timer_config(&timer_conf);

        // 配置 Pan 通道
        ledc_channel_config_t pan_conf = {
            .gpio_num = pan_gpio_,
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = LEDC_CHANNEL_0,
            .timer_sel = LEDC_TIMER_0,
            .duty = 0,
            .hpoint = 0
        };
        ledc_channel_config(&pan_conf);

        // 配置 Tilt 通道
        ledc_channel_config_t tilt_conf = {
            .gpio_num = tilt_gpio_,
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = LEDC_CHANNEL_1,
            .timer_sel = LEDC_TIMER_0,
            .duty = 0,
            .hpoint = 0
        };
        ledc_channel_config(&tilt_conf);
    }

    void SetAngle(int pan, int tilt) {
        // 角度转换为占空比 (0.5ms - 2.5ms 对应 0-180度)
        // 13位分辨率, 50Hz: 周期20ms
        // 0.5ms = 2.5%, 2.5ms = 12.5%
        int pan_duty = AngleToDuty(pan + 90);   // -90~90 转为 0~180
        int tilt_duty = AngleToDuty(tilt + 45); // -45~45 转为 0~90

        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, pan_duty);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);

        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, tilt_duty);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);

        pan_ = pan;
        tilt_ = tilt;
    }

    void ExecuteMotion(const std::string& motion) {
        if (motion == "neutral") {
            SetAngle(0, 0);
        } else if (motion == "nod") {
            // 点头动作序列
            SetAngle(0, 20);
            vTaskDelay(200 / portTICK_PERIOD_MS);
            SetAngle(0, -10);
            vTaskDelay(200 / portTICK_PERIOD_MS);
            SetAngle(0, 0);
        } else if (motion == "shake") {
            // 摇头动作序列
            SetAngle(30, 0);
            vTaskDelay(200 / portTICK_PERIOD_MS);
            SetAngle(-30, 0);
            vTaskDelay(200 / portTICK_PERIOD_MS);
            SetAngle(0, 0);
        }
        // ... 其他动作
    }

private:
    int AngleToDuty(int angle) {
        // 0度 = 2.5% duty, 180度 = 12.5% duty
        // 13位分辨率: 8191 max
        int min_duty = 205;   // 2.5% of 8191
        int max_duty = 1024;  // 12.5% of 8191
        return min_duty + (max_duty - min_duty) * angle / 180;
    }

    int pan_gpio_;
    int tilt_gpio_;
    int pan_ = 0;
    int tilt_ = 0;
};
```

---

## 服务器端命令格式

服务器（xiaozhi-esp32-server）发送的命令格式：

### 音量控制

```json
{"type": "iot", "commands": [{"name": "Speaker", "method": "SetVolume", "parameters": {"volume": 50}}]}
{"type": "iot", "commands": [{"name": "Speaker", "method": "VolumeUp"}]}
{"type": "iot", "commands": [{"name": "Speaker", "method": "VolumeDown"}]}
```

### 屏幕控制

```json
{"type": "iot", "commands": [{"name": "Screen", "method": "SetBrightness", "parameters": {"brightness": 80}}]}
{"type": "iot", "commands": [{"name": "Screen", "method": "TurnOff"}]}
```

### 舵机控制

```json
{"type": "iot", "commands": [{"name": "Servo", "method": "ExecuteMotion", "parameters": {"motion": "nod"}}]}
{"type": "iot", "commands": [{"name": "Servo", "method": "SetAngle", "parameters": {"pan": 30, "tilt": 15}}]}
```

### LED 控制

```json
{"type": "iot", "commands": [{"name": "LED", "method": "SetEffect", "parameters": {"effect": "rainbow"}}]}
{"type": "iot", "commands": [{"name": "LED", "method": "SetColor", "parameters": {"red": 255, "green": 0, "blue": 128}}]}
```

---

## 编译和烧录

```bash
cd /Users/good/Desktop/claude-projects/xiaozhi-esp32

# 编译
idf.py build

# 烧录
idf.py -p /dev/cu.usbserial-* flash

# 监控日志
idf.py -p /dev/cu.usbserial-* monitor
```

---

## 测试验证

### 1. 查看 ESP32 日志
```
I (12345) WS: Sending IoT descriptors
```

### 2. 服务器日志应显示
```
物联网描述更新: Speaker, Screen, Servo, LED
```

### 3. 调用 API 测试
```bash
curl -X POST -H "X-API-Key: mint-hardware-api-2025888999" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "YOUR_DEVICE_ID", "action": "up"}' \
  http://120.26.38.27:8003/api/v1/volume
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `Docs/mint-hardware-control.md` | 服务器端硬件控制文档 |
| `Docs/mint-openapi-schema.json` | Dify OpenAPI 规范 |
| `Docs/mint-firmware-upgrade-guide.md` | 本文档 |

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2024-12-30 | v1.0 | 初始版本 |
