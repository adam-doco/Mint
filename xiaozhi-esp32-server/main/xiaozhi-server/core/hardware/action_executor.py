"""
米特(Mint) 动作执行器
协调语音、表情、动作的同步执行
"""

import asyncio
from typing import Optional, Callable, Awaitable
from config.logger import setup_logging
from .action_protocol import ActionCommand, Motion, Emotion
from .action_parser import ActionParser
from .hardware_bridge import HardwareBridge

TAG = __name__
logger = setup_logging()


class ActionExecutor:
    """动作执行协调器"""

    def __init__(self, hardware_bridge: HardwareBridge):
        """
        初始化动作执行器

        Args:
            hardware_bridge: 硬件桥接对象
        """
        self.hardware = hardware_bridge
        self.is_executing = False
        self.action_queue = asyncio.Queue()
        self._executor_task: Optional[asyncio.Task] = None

        # 回调函数
        self._on_text_ready: Optional[Callable[[str], Awaitable]] = None
        self._on_action_start: Optional[Callable[[ActionCommand], Awaitable]] = None
        self._on_action_complete: Optional[Callable[[ActionCommand], Awaitable]] = None

    def set_text_callback(self, callback: Callable[[str], Awaitable]):
        """设置文本就绪回调（用于 TTS）"""
        self._on_text_ready = callback

    def set_action_callbacks(
        self,
        on_start: Optional[Callable[[ActionCommand], Awaitable]] = None,
        on_complete: Optional[Callable[[ActionCommand], Awaitable]] = None
    ):
        """设置动作回调"""
        self._on_action_start = on_start
        self._on_action_complete = on_complete

    async def start(self):
        """启动执行器"""
        if self._executor_task is None:
            self._executor_task = asyncio.create_task(self._executor_loop())
            logger.bind(tag=TAG).info("动作执行器已启动")

    async def stop(self):
        """停止执行器"""
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except asyncio.CancelledError:
                pass
            self._executor_task = None
            logger.bind(tag=TAG).info("动作执行器已停止")

    async def _executor_loop(self):
        """执行器主循环"""
        while True:
            try:
                action = await self.action_queue.get()
                await self._execute_action(action)
                self.action_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.bind(tag=TAG).error(f"执行动作时出错: {e}")

    async def process_llm_response(self, llm_response: str) -> str:
        """
        处理 LLM 回复，解析并执行动作

        Args:
            llm_response: LLM 的原始回复

        Returns:
            str: 用于 TTS 的纯文本
        """
        # 解析动作
        action_cmd, text = ActionParser.parse(llm_response)

        if action_cmd:
            # 将动作加入队列
            await self.action_queue.put(action_cmd)

            # 触发文本回调（用于 TTS）
            if self._on_text_ready and text:
                await self._on_text_ready(text)

            return text
        else:
            # 没有解析到动作，返回原始文本
            if self._on_text_ready:
                await self._on_text_ready(llm_response)
            return llm_response

    async def execute_now(self, action: ActionCommand):
        """
        立即执行动作（跳过队列）

        Args:
            action: 动作命令
        """
        await self._execute_action(action)

    async def _execute_action(self, action: ActionCommand):
        """
        执行单个动作

        Args:
            action: 动作命令
        """
        self.is_executing = True

        try:
            # 触发开始回调
            if self._on_action_start:
                await self._on_action_start(action)

            logger.bind(tag=TAG).info(
                f"开始执行动作: motion={action.motion.value}, "
                f"emotion={action.emotion.value}, led={action.led}"
            )

            # 执行硬件动作
            await self.hardware.execute_action(action)

            # 触发完成回调
            if self._on_action_complete:
                await self._on_action_complete(action)

            logger.bind(tag=TAG).debug("动作执行完成")

        except Exception as e:
            logger.bind(tag=TAG).error(f"执行动作失败: {e}")

        finally:
            self.is_executing = False

    async def execute_motion(self, motion_name: str):
        """
        执行单独的舵机动作

        Args:
            motion_name: 动作名称
        """
        try:
            motion = Motion(motion_name)
            await self.hardware.execute_motion(motion)
        except ValueError:
            logger.bind(tag=TAG).warning(f"未知动作: {motion_name}")

    async def set_emotion(self, emotion_name: str):
        """
        设置单独的表情

        Args:
            emotion_name: 表情名称
        """
        try:
            emotion = Emotion(emotion_name)
            await self.hardware.set_emotion(emotion)
        except ValueError:
            logger.bind(tag=TAG).warning(f"未知表情: {emotion_name}")

    async def set_led(self, effect_name: str):
        """
        设置单独的 LED 灯效

        Args:
            effect_name: 灯效名称
        """
        await self.hardware.set_led_effect(effect_name)

    async def idle(self):
        """进入待机状态"""
        await self.hardware.reset_to_idle()

    async def listening(self):
        """进入聆听状态"""
        await asyncio.gather(
            self.hardware.set_emotion(Emotion.NEUTRAL),
            self.hardware.set_led_effect("pulse_blue")
        )

    async def thinking(self):
        """进入思考状态"""
        await asyncio.gather(
            self.hardware.execute_motion(Motion.TILT_RIGHT),
            self.hardware.set_emotion(Emotion.THINKING),
            self.hardware.set_led_effect("spin_purple")
        )

    async def speaking(self):
        """进入说话状态"""
        await self.hardware.set_led_effect("breathing_cyan")

    async def greeting(self):
        """执行打招呼动作"""
        action = ActionCommand(
            text="",
            motion=Motion.GREETING,
            emotion=Emotion.HAPPY,
            led="rainbow"
        )
        await self.execute_now(action)
