"""
米特(Mint) 动作协议定义
定义所有舵机动作、眼睛表情、LED 灯效的常量和映射
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ============== 舵机动作系统 ==============

class Motion(Enum):
    """舵机动作枚举"""
    NEUTRAL = "neutral"          # 回正
    NOD = "nod"                  # 点头
    SHAKE = "shake"              # 摇头
    TILT_LEFT = "tilt_left"      # 左歪头
    TILT_RIGHT = "tilt_right"    # 右歪头
    LOOK_UP = "look_up"          # 抬头
    LOOK_DOWN = "look_down"      # 低头
    LOOK_LEFT = "look_left"      # 向左看
    LOOK_RIGHT = "look_right"    # 向右看
    EXCITED = "excited"          # 兴奋抖动
    SHY = "shy"                  # 害羞
    GREETING = "greeting"        # 打招呼


@dataclass
class ServoPosition:
    """舵机位置"""
    pitch: int = 0  # 俯仰角度 (-30 ~ +30)
    yaw: int = 0    # 偏航角度 (-45 ~ +45)


@dataclass
class MotionSequence:
    """动作序列"""
    positions: List[ServoPosition]  # 位置列表
    duration_ms: int = 200          # 每步持续时间(毫秒)


# 动作到舵机序列的映射
MOTION_SEQUENCES = {
    Motion.NEUTRAL: MotionSequence(
        positions=[ServoPosition(0, 0)],
        duration_ms=300
    ),
    Motion.NOD: MotionSequence(
        positions=[
            ServoPosition(-20, 0),
            ServoPosition(0, 0),
            ServoPosition(-20, 0),
            ServoPosition(0, 0),
        ],
        duration_ms=150
    ),
    Motion.SHAKE: MotionSequence(
        positions=[
            ServoPosition(0, -30),
            ServoPosition(0, 30),
            ServoPosition(0, -30),
            ServoPosition(0, 30),
            ServoPosition(0, 0),
        ],
        duration_ms=120
    ),
    Motion.TILT_LEFT: MotionSequence(
        positions=[ServoPosition(15, -20)],
        duration_ms=300
    ),
    Motion.TILT_RIGHT: MotionSequence(
        positions=[ServoPosition(15, 20)],
        duration_ms=300
    ),
    Motion.LOOK_UP: MotionSequence(
        positions=[ServoPosition(25, 0)],
        duration_ms=300
    ),
    Motion.LOOK_DOWN: MotionSequence(
        positions=[ServoPosition(-25, 0)],
        duration_ms=300
    ),
    Motion.LOOK_LEFT: MotionSequence(
        positions=[ServoPosition(0, -35)],
        duration_ms=300
    ),
    Motion.LOOK_RIGHT: MotionSequence(
        positions=[ServoPosition(0, 35)],
        duration_ms=300
    ),
    Motion.EXCITED: MotionSequence(
        positions=[
            ServoPosition(10, 0),
            ServoPosition(-10, 0),
            ServoPosition(10, 0),
            ServoPosition(-10, 0),
            ServoPosition(0, 0),
        ],
        duration_ms=80
    ),
    Motion.SHY: MotionSequence(
        positions=[ServoPosition(-15, -25)],
        duration_ms=400
    ),
    Motion.GREETING: MotionSequence(
        positions=[
            ServoPosition(-15, 0),
            ServoPosition(0, -20),
            ServoPosition(0, 20),
            ServoPosition(0, 0),
        ],
        duration_ms=200
    ),
}


# ============== 眼睛表情系统 ==============

class Emotion(Enum):
    """眼睛表情枚举"""
    NEUTRAL = "neutral"          # 正常
    HAPPY = "happy"              # 开心
    SAD = "sad"                  # 难过
    ANGRY = "angry"              # 生气
    SURPRISED = "surprised"      # 惊讶
    SLEEPY = "sleepy"            # 困倦
    THINKING = "thinking"        # 思考
    LOVE = "love"                # 爱心
    DOUBT = "doubt"              # 怀疑
    SCARED = "scared"            # 害怕
    PROUD = "proud"              # 得意
    SPEECHLESS = "speechless"    # 无语
    BLINK = "blink"              # 眨眼(动画)
    WINK = "wink"                # 眨单眼(动画)


@dataclass
class EyeState:
    """眼睛状态"""
    # 眼睛形状参数
    open_ratio: float = 1.0      # 睁眼程度 0~1
    pupil_size: float = 1.0      # 瞳孔大小 0.5~1.5
    pupil_x: float = 0.0         # 瞳孔X偏移 -1~1
    pupil_y: float = 0.0         # 瞳孔Y偏移 -1~1
    eyebrow_angle: float = 0.0   # 眉毛角度 -30~30
    # 特殊形状
    shape: str = "round"         # 形状: round, arc, heart, line


# 表情到眼睛状态的映射
EMOTION_STATES = {
    Emotion.NEUTRAL: EyeState(open_ratio=1.0, pupil_size=1.0),
    Emotion.HAPPY: EyeState(open_ratio=0.3, shape="arc"),
    Emotion.SAD: EyeState(open_ratio=0.7, pupil_y=0.3, eyebrow_angle=-15),
    Emotion.ANGRY: EyeState(open_ratio=0.6, pupil_size=0.8, eyebrow_angle=25),
    Emotion.SURPRISED: EyeState(open_ratio=1.0, pupil_size=1.4),
    Emotion.SLEEPY: EyeState(open_ratio=0.3, pupil_size=0.9),
    Emotion.THINKING: EyeState(open_ratio=0.9, pupil_x=0.4, pupil_y=-0.3),
    Emotion.LOVE: EyeState(open_ratio=1.0, shape="heart"),
    Emotion.DOUBT: EyeState(open_ratio=0.7, pupil_x=-0.2, eyebrow_angle=10),
    Emotion.SCARED: EyeState(open_ratio=1.0, pupil_size=0.6),
    Emotion.PROUD: EyeState(open_ratio=0.5, pupil_y=-0.2, shape="arc"),
    Emotion.SPEECHLESS: EyeState(open_ratio=0.1, shape="line"),
}


# ============== LED 灯效系统 ==============

class LedMode(Enum):
    """LED 模式枚举"""
    OFF = "off"
    SOLID = "solid"
    BREATHING = "breathing"
    PULSE = "pulse"
    RAINBOW = "rainbow"
    SPIN = "spin"
    BLINK = "blink"
    CHASE = "chase"


class LedColor(Enum):
    """LED 预设颜色"""
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    PURPLE = (128, 0, 128)
    ORANGE = (255, 165, 0)
    PINK = (255, 192, 203)


@dataclass
class LedEffect:
    """LED 灯效配置"""
    mode: LedMode = LedMode.OFF
    color: Tuple[int, int, int] = (0, 255, 255)  # RGB
    speed: int = 50      # 动画速度 1-100
    brightness: int = 80  # 亮度 0-100


# 灯效字符串到配置的映射
LED_EFFECTS = {
    "off": LedEffect(mode=LedMode.OFF),
    # 呼吸灯效
    "breathing_white": LedEffect(mode=LedMode.BREATHING, color=LedColor.WHITE.value),
    "breathing_cyan": LedEffect(mode=LedMode.BREATHING, color=LedColor.CYAN.value),
    "breathing_blue": LedEffect(mode=LedMode.BREATHING, color=LedColor.BLUE.value),
    "breathing_pink": LedEffect(mode=LedMode.BREATHING, color=LedColor.PINK.value),
    "breathing_green": LedEffect(mode=LedMode.BREATHING, color=LedColor.GREEN.value),
    "breathing_orange": LedEffect(mode=LedMode.BREATHING, color=LedColor.ORANGE.value),
    # 脉冲灯效
    "pulse_blue": LedEffect(mode=LedMode.PULSE, color=LedColor.BLUE.value, speed=70),
    "pulse_green": LedEffect(mode=LedMode.PULSE, color=LedColor.GREEN.value, speed=70),
    "pulse_red": LedEffect(mode=LedMode.PULSE, color=LedColor.RED.value, speed=70),
    # 彩虹
    "rainbow": LedEffect(mode=LedMode.RAINBOW),
    # 旋转
    "spin_purple": LedEffect(mode=LedMode.SPIN, color=LedColor.PURPLE.value),
    "spin_cyan": LedEffect(mode=LedMode.SPIN, color=LedColor.CYAN.value),
    # 闪烁
    "blink_yellow": LedEffect(mode=LedMode.BLINK, color=LedColor.YELLOW.value),
    "blink_red": LedEffect(mode=LedMode.BLINK, color=LedColor.RED.value),
    # 常亮
    "solid_white": LedEffect(mode=LedMode.SOLID, color=LedColor.WHITE.value),
    "solid_cyan": LedEffect(mode=LedMode.SOLID, color=LedColor.CYAN.value),
}


# ============== 动作命令数据结构 ==============

@dataclass
class ActionCommand:
    """完整的动作命令"""
    text: str                           # 语音文本
    motion: Motion = Motion.NEUTRAL     # 舵机动作
    emotion: Emotion = Emotion.NEUTRAL  # 眼睛表情
    led: str = "breathing_cyan"         # LED 灯效

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionCommand':
        """从字典创建动作命令"""
        return cls(
            text=data.get("text", ""),
            motion=Motion(data.get("motion", "neutral")),
            emotion=Emotion(data.get("emotion", "neutral")),
            led=data.get("led", "breathing_cyan")
        )

    def get_motion_sequence(self) -> Optional[MotionSequence]:
        """获取舵机动作序列"""
        return MOTION_SEQUENCES.get(self.motion)

    def get_eye_state(self) -> Optional[EyeState]:
        """获取眼睛状态"""
        return EMOTION_STATES.get(self.emotion)

    def get_led_effect(self) -> LedEffect:
        """获取 LED 灯效配置"""
        return LED_EFFECTS.get(self.led, LED_EFFECTS["breathing_cyan"])
