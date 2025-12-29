"""
米特(Mint) 硬件通信桥接
负责与 ESP32 主控和 ESP32-C3 副控的通信
"""

import json
import asyncio
import serial
import serial.tools.list_ports
from typing import Optional, Callable, Any
from config.logger import setup_logging
from .action_protocol import (
    ActionCommand,
    Motion,
    Emotion,
    LedEffect,
    MOTION_SEQUENCES,
    EMOTION_STATES,
    LED_EFFECTS,
    ServoPosition
)

TAG = __name__
logger = setup_logging()


class HardwareBridge:
    """硬件通信桥接类"""

    def __init__(self, config: dict = None):
        """
        初始化硬件桥接

        Args:
            config: 配置字典，包含：
                - serial_port: 串口端口 (如 /dev/ttyUSB0)
                - serial_baudrate: 波特率 (默认 115200)
                - websocket_conn: WebSocket 连接对象
        """
        self.config = config or {}
        self.serial_port = self.config.get("serial_port")
        self.serial_baudrate = self.config.get("serial_baudrate", 115200)
        self.serial_conn: Optional[serial.Serial] = None
        self.websocket_conn = None

        # 当前状态
        self.current_motion = Motion.NEUTRAL
        self.current_emotion = Emotion.NEUTRAL
        self.current_led = "breathing_cyan"

    async def initialize(self):
        """初始化硬件连接"""
        # 初始化串口连接（连接 ESP32-C3 表情控制器）
        if self.serial_port:
            await self._init_serial()
        else:
            # 自动检测串口
            await self._auto_detect_serial()

        logger.bind(tag=TAG).info("硬件桥接初始化完成")

    async def _init_serial(self):
        """初始化串口连接"""
        try:
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.serial_baudrate,
                timeout=1
            )
            logger.bind(tag=TAG).info(f"串口已连接: {self.serial_port}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"串口连接失败: {e}")
            self.serial_conn = None

    async def _auto_detect_serial(self):
        """自动检测串口"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # 检测常见的 ESP32 串口特征
            if "USB" in port.description or "CP210" in port.description or "CH340" in port.description:
                self.serial_port = port.device
                logger.bind(tag=TAG).info(f"自动检测到串口: {port.device} - {port.description}")
                await self._init_serial()
                return

        logger.bind(tag=TAG).warning("未检测到可用串口，表情控制将不可用")

    def set_websocket(self, conn):
        """设置 WebSocket 连接"""
        self.websocket_conn = conn

    # ==================== 舵机控制 ====================

    async def execute_motion(self, motion: Motion, speed: str = "normal"):
        """
        执行舵机动作

        Args:
            motion: 动作类型
            speed: 速度 (slow/normal/fast)
        """
        sequence = MOTION_SEQUENCES.get(motion)
        if not sequence:
            logger.bind(tag=TAG).warning(f"未知动作: {motion}")
            return

        self.current_motion = motion
        logger.bind(tag=TAG).info(f"执行动作: {motion.value}")

        # 计算速度倍率
        speed_multiplier = {"slow": 1.5, "normal": 1.0, "fast": 0.6}.get(speed, 1.0)

        # 执行动作序列
        for position in sequence.positions:
            await self._send_servo_command(position)
            await asyncio.sleep(sequence.duration_ms * speed_multiplier / 1000)

    async def _send_servo_command(self, position: ServoPosition):
        """
        发送舵机控制命令到 ESP32

        Args:
            position: 舵机位置
        """
        command = {
            "type": "servo",
            "pitch": position.pitch,
            "yaw": position.yaw
        }

        # 通过 WebSocket 发送到主 ESP32
        if self.websocket_conn:
            try:
                await self.websocket_conn.send(json.dumps(command))
                logger.bind(tag=TAG).debug(f"舵机命令已发送: P={position.pitch}, Y={position.yaw}")
            except Exception as e:
                logger.bind(tag=TAG).error(f"发送舵机命令失败: {e}")

    async def set_servo_position(self, pitch: int, yaw: int):
        """
        直接设置舵机角度

        Args:
            pitch: 俯仰角度 (-30 ~ +30)
            yaw: 偏航角度 (-45 ~ +45)
        """
        # 限制角度范围
        pitch = max(-30, min(30, pitch))
        yaw = max(-45, min(45, yaw))

        await self._send_servo_command(ServoPosition(pitch, yaw))

    # ==================== 表情控制 ====================

    async def set_emotion(self, emotion: Emotion):
        """
        设置眼睛表情

        Args:
            emotion: 表情类型
        """
        self.current_emotion = emotion
        logger.bind(tag=TAG).info(f"设置表情: {emotion.value}")

        # 通过串口发送表情代码到 ESP32-C3
        command = f"FACE:{emotion.value}\n"
        await self._send_serial_command(command)

    async def _send_serial_command(self, command: str):
        """
        通过串口发送命令到 ESP32-C3

        Args:
            command: 命令字符串
        """
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode())
                logger.bind(tag=TAG).debug(f"串口命令已发送: {command.strip()}")
            except Exception as e:
                logger.bind(tag=TAG).error(f"发送串口命令失败: {e}")
        else:
            logger.bind(tag=TAG).debug(f"串口未连接，命令被忽略: {command.strip()}")

    async def trigger_blink(self):
        """触发眨眼动画"""
        await self._send_serial_command("ANIM:blink\n")

    async def trigger_wink(self):
        """触发眨单眼动画"""
        await self._send_serial_command("ANIM:wink\n")

    # ==================== LED 控制 ====================

    async def set_led_effect(self, effect_name: str):
        """
        设置 LED 灯效

        Args:
            effect_name: 灯效名称 (如 breathing_cyan)
        """
        effect = LED_EFFECTS.get(effect_name)
        if not effect:
            logger.bind(tag=TAG).warning(f"未知灯效: {effect_name}")
            return

        self.current_led = effect_name
        logger.bind(tag=TAG).info(f"设置灯效: {effect_name}")

        # 构建 LED 命令
        r, g, b = effect.color
        command = f"LED:{effect.mode.value},{r},{g},{b},{effect.speed},{effect.brightness}\n"
        await self._send_serial_command(command)

    async def set_led_color(self, r: int, g: int, b: int, mode: str = "solid"):
        """
        直接设置 LED 颜色

        Args:
            r, g, b: RGB 颜色值 (0-255)
            mode: 模式 (solid/breathing/pulse)
        """
        command = f"LED:{mode},{r},{g},{b},50,80\n"
        await self._send_serial_command(command)

    async def turn_off_led(self):
        """关闭 LED"""
        await self.set_led_effect("off")

    # ==================== 组合动作 ====================

    async def execute_action(self, action: ActionCommand):
        """
        执行完整的动作命令

        Args:
            action: 动作命令对象
        """
        logger.bind(tag=TAG).info(
            f"执行组合动作: motion={action.motion.value}, "
            f"emotion={action.emotion.value}, led={action.led}"
        )

        # 并行执行所有动作
        await asyncio.gather(
            self.execute_motion(action.motion),
            self.set_emotion(action.emotion),
            self.set_led_effect(action.led)
        )

    async def reset_to_idle(self):
        """重置到待机状态"""
        await asyncio.gather(
            self.execute_motion(Motion.NEUTRAL),
            self.set_emotion(Emotion.NEUTRAL),
            self.set_led_effect("breathing_cyan")
        )

    # ==================== 资源清理 ====================

    async def close(self):
        """关闭所有连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.bind(tag=TAG).info("串口连接已关闭")

        self.websocket_conn = None
        logger.bind(tag=TAG).info("硬件桥接已关闭")
