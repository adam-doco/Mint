# 米特(Mint) 动作控制协议设计文档

## 1. JSON 动作协议格式

### 1.1 完整格式定义

LLM 返回的每条消息应包含以下结构：

```json
{
  "text": "要说的话",
  "motion": "动作名称",
  "emotion": "表情名称",
  "led": "灯效名称"
}
```

### 1.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 语音合成的文本内容 |
| `motion` | string | 否 | 舵机动作，默认 `neutral` |
| `emotion` | string | 否 | 眼睛表情，默认 `neutral` |
| `led` | string | 否 | LED 灯效，默认 `off` |

### 1.3 示例

```json
{
  "text": "你好呀！我是米特，很高兴认识你！",
  "motion": "nod",
  "emotion": "happy",
  "led": "breathing_cyan"
}
```

```json
{
  "text": "让我想想这个问题...",
  "motion": "tilt_right",
  "emotion": "thinking",
  "led": "pulse_blue"
}
```

```json
{
  "text": "哇，这也太厉害了吧！",
  "motion": "look_up",
  "emotion": "surprised",
  "led": "rainbow"
}
```

---

## 2. 舵机动作系统 (Motion System)

### 2.1 硬件配置

| 舵机 | 控制轴 | 角度范围 | 默认位置 | 说明 |
|------|--------|----------|----------|------|
| Servo 1 | Pitch (俯仰) | -30° ~ +30° | 0° | 正值抬头，负值低头 |
| Servo 2 | Yaw (偏航) | -45° ~ +45° | 0° | 正值向右，负值向左 |

### 2.2 预设动作列表

| 动作名称 | 标识符 | 动作序列 | 说明 |
|----------|--------|----------|------|
| 回正 | `neutral` | `P:0, Y:0` | 头部回到正中位置 |
| 点头 | `nod` | `P:0→-20→0→-20→0` | 连续点头两次 |
| 摇头 | `shake` | `Y:0→-30→30→-30→30→0` | 左右摇头 |
| 左歪头 | `tilt_left` | `P:15, Y:-20` | 向左歪头，表示好奇 |
| 右歪头 | `tilt_right` | `P:15, Y:20` | 向右歪头，表示好奇 |
| 抬头 | `look_up` | `P:25, Y:0` | 抬头看 |
| 低头 | `look_down` | `P:-25, Y:0` | 低头看 |
| 向左看 | `look_left` | `P:0, Y:-35` | 转向左边 |
| 向右看 | `look_right` | `P:0, Y:35` | 转向右边 |
| 兴奋抖动 | `excited` | `P:0→10→-10→10→-10→0` | 快速小幅度抖动 |
| 害羞 | `shy` | `P:-15, Y:-25` | 低头偏向一边 |
| 打招呼 | `greeting` | `nod` + `Y:0→-20→20→0` | 点头+轻微左右 |

### 2.3 动作参数

每个动作可以附加速度参数：

| 速度 | 标识符 | 说明 |
|------|--------|------|
| 慢速 | `slow` | 动作缓慢，适合温柔场景 |
| 正常 | `normal` | 默认速度 |
| 快速 | `fast` | 动作迅速，适合兴奋场景 |

---

## 3. 眼睛表情系统 (Emotion System)

### 3.1 硬件配置

- 显示屏：2x GC9A01 圆形 LCD (240x240)
- 布局：左眼 + 右眼
- 通信：SPI 接口

### 3.2 表情状态列表

| 表情名称 | 标识符 | 眼睛形态 | 适用场景 |
|----------|--------|----------|----------|
| 正常 | `neutral` | 圆形瞳孔，正常大小 | 默认状态 |
| 开心 | `happy` | 眯眼，弯成弧形 | 高兴、打招呼 |
| 难过 | `sad` | 眼角下垂，瞳孔偏下 | 沮丧、道歉 |
| 生气 | `angry` | 眉头紧皱，眼睛变窄 | 不满、抱怨 |
| 惊讶 | `surprised` | 瞳孔放大，眼睛睁圆 | 震惊、意外 |
| 困倦 | `sleepy` | 眼睛半闭，缓慢眨眼 | 疲惫、无聊 |
| 思考 | `thinking` | 瞳孔偏向一侧上方 | 思考、回忆 |
| 爱心 | `love` | 瞳孔变成爱心形状 | 喜欢、崇拜 |
| 怀疑 | `doubt` | 一只眼睛微眯 | 质疑、不信 |
| 害怕 | `scared` | 瞳孔缩小，眼白增多 | 恐惧、紧张 |
| 得意 | `proud` | 眼睛微眯，嘴角上扬感 | 自豪、炫耀 |
| 无语 | `speechless` | 眼睛变成横线 | 无奈、尴尬 |

### 3.3 眼睛动画

| 动画名称 | 标识符 | 描述 | 时长 |
|----------|--------|------|------|
| 眨眼 | `blink` | 双眼同时闭合再睁开 | 200ms |
| 眨单眼 | `wink` | 右眼眨一下 | 300ms |
| 转眼珠 | `roll` | 瞳孔绕圈转动 | 800ms |
| 放大缩小 | `pulse` | 瞳孔有节奏放大缩小 | 循环 |

### 3.4 眼睛颜色主题

| 主题 | 标识符 | 瞳孔颜色 | 说明 |
|------|--------|----------|------|
| 默认 | `default` | 青色 #00FFFF | 科技感 |
| 温暖 | `warm` | 橙色 #FFA500 | 亲切 |
| 冷静 | `cool` | 蓝色 #4169E1 | 沉稳 |
| 警告 | `warning` | 红色 #FF4444 | 警示 |
| 自然 | `nature` | 绿色 #32CD32 | 平和 |

---

## 4. LED 灯效系统 (LED System)

### 4.1 硬件配置

- LED 型号：WS2812B
- 数量：环绕每只眼睛（建议每边 12-16 颗）
- 控制：通过 ESP32 GPIO

### 4.2 灯效模式

| 模式名称 | 标识符 | 描述 |
|----------|--------|------|
| 关闭 | `off` | LED 全部熄灭 |
| 常亮 | `solid_{color}` | 单色常亮 |
| 呼吸 | `breathing_{color}` | 渐亮渐暗循环 |
| 脉冲 | `pulse_{color}` | 快速闪烁 |
| 彩虹 | `rainbow` | 彩虹色流动 |
| 旋转 | `spin_{color}` | 颜色环形旋转 |
| 闪烁 | `blink_{color}` | 有节奏闪烁 |
| 渐变 | `gradient` | 多色渐变 |
| 追逐 | `chase_{color}` | 光点追逐效果 |
| 呼吸彩虹 | `rainbow_breathing` | 彩虹色呼吸 |

### 4.3 预设颜色

| 颜色名称 | 标识符 | RGB 值 | 使用场景 |
|----------|--------|--------|----------|
| 白色 | `white` | #FFFFFF | 通用 |
| 红色 | `red` | #FF0000 | 警告、生气 |
| 绿色 | `green` | #00FF00 | 成功、开心 |
| 蓝色 | `blue` | #0000FF | 思考、冷静 |
| 黄色 | `yellow` | #FFFF00 | 提醒、注意 |
| 青色 | `cyan` | #00FFFF | 默认、科技感 |
| 紫色 | `purple` | #800080 | 神秘、特殊 |
| 橙色 | `orange` | #FFA500 | 温暖、友好 |
| 粉色 | `pink` | #FFC0CB | 可爱、害羞 |

### 4.4 灯效与情绪映射建议

| 情绪场景 | 推荐灯效 |
|----------|----------|
| 待机/空闲 | `breathing_cyan` |
| 聆听中 | `pulse_blue` |
| 思考中 | `spin_purple` |
| 开心 | `rainbow` |
| 难过 | `breathing_blue` |
| 生气 | `pulse_red` |
| 惊讶 | `blink_yellow` |
| 警告 | `blink_red` |

---

## 5. 动作组合 (Action Presets)

### 5.1 常用组合

| 场景 | motion | emotion | led |
|------|--------|---------|-----|
| 打招呼 | `greeting` | `happy` | `rainbow` |
| 思考 | `tilt_right` | `thinking` | `spin_purple` |
| 肯定 | `nod` | `happy` | `pulse_green` |
| 否定 | `shake` | `neutral` | `breathing_blue` |
| 不懂 | `tilt_left` | `doubt` | `breathing_orange` |
| 难过 | `look_down` | `sad` | `breathing_blue` |
| 兴奋 | `excited` | `surprised` | `rainbow` |
| 害羞 | `shy` | `happy` | `breathing_pink` |
| 待机 | `neutral` | `neutral` | `breathing_cyan` |
| 聆听 | `neutral` | `neutral` | `pulse_blue` |

---

## 6. Dify 提示词参考

在 Dify 的系统提示词中添加：

```
你是米特(Mint)，一个可爱的桌面AI台灯助手。

【输出格式要求 - 必须严格遵守】
每次回复必须按以下格式：
1. 先输出你要说的话（纯文本）
2. 最后用 [ACT] 标记，后面跟动作 JSON

格式示例：
你好呀！我是米特，很高兴认识你！今天有什么想聊的？
[ACT]{"motion": "greeting", "emotion": "happy", "led": "rainbow"}

注意：[ACT] 和 JSON 之间不要有空格或换行！

【可用动作 motion】
- neutral: 回正
- nod: 点头
- shake: 摇头
- tilt_left: 左歪头（好奇）
- tilt_right: 右歪头（好奇）
- look_up: 抬头
- look_down: 低头
- excited: 兴奋抖动
- shy: 害羞
- greeting: 打招呼

【可用表情 emotion】
- neutral: 正常
- happy: 开心
- sad: 难过
- angry: 生气
- surprised: 惊讶
- sleepy: 困倦
- thinking: 思考
- love: 爱心
- doubt: 怀疑
- proud: 得意
- speechless: 无语

【可用灯效 led】
- breathing_cyan: 青色呼吸（默认）
- breathing_blue: 蓝色呼吸
- breathing_pink: 粉色呼吸
- pulse_blue: 蓝色脉冲
- pulse_green: 绿色脉冲
- rainbow: 彩虹
- spin_purple: 紫色旋转

请根据对话内容和情感，选择合适的动作、表情和灯效。
```

---

## 7. 版本记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2024-12-29 | 初始设计，包含舵机、表情、LED 基础系统 |
