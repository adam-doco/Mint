"""
硬件控制 HTTP API 处理器
供 Dify 等外部服务调用，控制米特的硬件
"""

import json
import asyncio
import secrets
from aiohttp import web
from core.api.base_handler import BaseHandler
from core.connection_registry import connection_registry
from config.logger import setup_logging

TAG = __name__


class HardwareHandler(BaseHandler):
    """硬件控制 HTTP API 处理器"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = setup_logging()
        # 从配置中获取 API Key，如果没有配置则生成一个随机的
        hardware_api_config = config.get("hardware_api", {})
        self.api_key = hardware_api_config.get("api_key", None)
        self.auth_enabled = hardware_api_config.get("enabled", True)

        # 如果没有配置 API Key，生成一个随机的并记录到日志
        if self.auth_enabled and not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
            self.logger.bind(tag=TAG).warning(
                f"未配置 hardware_api.api_key，已自动生成临时 API Key: {self.api_key}"
            )
            self.logger.bind(tag=TAG).warning(
                "请在 config.yaml 中配置 hardware_api.api_key 以使用固定的 API Key"
            )

    def _verify_api_key(self, request) -> bool:
        """
        验证 API Key

        支持两种方式传递 API Key:
        1. Authorization: Bearer <api_key>
        2. X-API-Key: <api_key>

        Args:
            request: HTTP 请求对象

        Returns:
            验证是否通过
        """
        if not self.auth_enabled:
            return True

        # 方式1: Authorization: Bearer <api_key>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if secrets.compare_digest(token, self.api_key):
                return True

        # 方式2: X-API-Key: <api_key>
        api_key_header = request.headers.get("X-API-Key", "")
        if api_key_header and secrets.compare_digest(api_key_header, self.api_key):
            return True

        return False

    def _unauthorized_response(self):
        """返回未授权响应"""
        response = web.json_response(
            {"success": False, "error": "未授权访问，请提供有效的 API Key"},
            status=401
        )
        self._add_cors_headers(response)
        return response

    async def handle_options(self, request):
        """处理 OPTIONS 请求"""
        response = web.Response(body=b"", content_type="text/plain")
        self._add_cors_headers(response)
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, X-API-Key, Content-Type, device-id, client-id"
        )
        return response

    async def _send_iot_command(self, device_id: str, command: dict) -> dict:
        """
        发送 IoT 命令到设备

        Args:
            device_id: 设备ID
            command: IoT 命令

        Returns:
            执行结果
        """
        conn = connection_registry.get_connection(device_id)
        if not conn:
            return {"success": False, "error": f"设备 {device_id} 未连接"}

        if not hasattr(conn, 'websocket') or not conn.websocket:
            return {"success": False, "error": "设备 WebSocket 连接不可用"}

        try:
            message = json.dumps({
                "type": "iot",
                "commands": [command]
            })
            await conn.websocket.send(message)
            self.logger.bind(tag=TAG).info(f"IoT 命令已发送到 {device_id}: {command}")
            return {"success": True, "message": "命令已发送"}
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送命令失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 设备状态 ====================

    async def handle_devices(self, request):
        """获取所有已连接设备列表"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        devices = connection_registry.get_all_device_ids()
        response = web.json_response({
            "success": True,
            "devices": devices,
            "count": len(devices)
        })
        self._add_cors_headers(response)
        return response

    # ==================== 音量控制 ====================

    async def handle_volume(self, request):
        """控制音量"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            action = data.get("action", "set")
            value = data.get("value", 50)

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            command = {"name": "Speaker", "method": "", "parameters": {}}

            if action == "set":
                value = max(0, min(100, value))
                command["method"] = "SetVolume"
                command["parameters"]["volume"] = value
                msg = f"音量已调整到 {value}"
            elif action == "up":
                command["method"] = "VolumeUp"
                msg = "音量已调大"
            elif action == "down":
                command["method"] = "VolumeDown"
                msg = "音量已调小"
            elif action == "mute":
                command["method"] = "Mute"
                msg = "已静音"
            elif action == "unmute":
                command["method"] = "Unmute"
                msg = "已取消静音"
            else:
                return web.json_response(
                    {"success": False, "error": f"不支持的操作: {action}"},
                    status=400
                )

            result = await self._send_iot_command(device_id, command)
            result["message"] = msg if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"音量控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    # ==================== 屏幕控制 ====================

    async def handle_brightness(self, request):
        """控制屏幕亮度"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            action = data.get("action", "set")
            value = data.get("value", 80)

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            command = {"name": "Screen", "method": "", "parameters": {}}

            if action == "set":
                value = max(0, min(100, value))
                command["method"] = "SetBrightness"
                command["parameters"]["brightness"] = value
                msg = f"屏幕亮度已调整到 {value}"
            elif action == "up":
                command["method"] = "BrightnessUp"
                msg = "屏幕已调亮"
            elif action == "down":
                command["method"] = "BrightnessDown"
                msg = "屏幕已调暗"
            else:
                return web.json_response(
                    {"success": False, "error": f"不支持的操作: {action}"},
                    status=400
                )

            result = await self._send_iot_command(device_id, command)
            result["message"] = msg if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"亮度控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    async def handle_screen_power(self, request):
        """控制屏幕开关"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            power = data.get("power", "on")

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            command = {
                "name": "Screen",
                "method": "TurnOn" if power == "on" else "TurnOff",
                "parameters": {}
            }
            msg = "屏幕已打开" if power == "on" else "屏幕已关闭"

            result = await self._send_iot_command(device_id, command)
            result["message"] = msg if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"屏幕开关控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    # ==================== 动作控制 ====================

    async def handle_motion(self, request):
        """控制舵机动作"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            motion = data.get("motion", "neutral")

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            valid_motions = [
                "neutral", "nod", "shake", "tilt_left", "tilt_right",
                "look_up", "look_down", "look_left", "look_right",
                "excited", "shy", "greeting"
            ]
            if motion not in valid_motions:
                return web.json_response(
                    {"success": False, "error": f"不支持的动作: {motion}"},
                    status=400
                )

            command = {
                "name": "Servo",
                "method": "ExecuteMotion",
                "parameters": {"motion": motion}
            }

            result = await self._send_iot_command(device_id, command)
            result["message"] = f"动作 {motion} 已执行" if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"动作控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    # ==================== 表情控制 ====================

    async def handle_emotion(self, request):
        """控制表情"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            emotion = data.get("emotion", "neutral")

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            valid_emotions = [
                "neutral", "happy", "sad", "angry", "surprised", "sleepy",
                "thinking", "love", "doubt", "scared", "proud", "speechless"
            ]
            if emotion not in valid_emotions:
                return web.json_response(
                    {"success": False, "error": f"不支持的表情: {emotion}"},
                    status=400
                )

            command = {
                "name": "Expression",
                "method": "SetEmotion",
                "parameters": {"emotion": emotion}
            }

            result = await self._send_iot_command(device_id, command)
            result["message"] = f"表情已切换为 {emotion}" if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"表情控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    # ==================== LED 控制 ====================

    async def handle_led(self, request):
        """控制 LED 灯效"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            effect = data.get("effect", "default")

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            valid_effects = [
                "default", "rainbow", "breathing", "pulse", "sparkle", "wave",
                "fire", "ocean", "forest", "sunset", "aurora", "party",
                "relax", "focus", "sleep", "alert"
            ]
            if effect not in valid_effects:
                return web.json_response(
                    {"success": False, "error": f"不支持的灯效: {effect}"},
                    status=400
                )

            command = {
                "name": "LED",
                "method": "SetEffect",
                "parameters": {"effect": effect}
            }

            result = await self._send_iot_command(device_id, command)
            result["message"] = f"灯效已切换为 {effect}" if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LED 控制出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )

    async def handle_led_color(self, request):
        """设置 LED 自定义颜色"""
        # 验证 API Key
        if not self._verify_api_key(request):
            return self._unauthorized_response()

        try:
            data = await request.json()
            device_id = data.get("device_id")
            red = data.get("red", 255)
            green = data.get("green", 255)
            blue = data.get("blue", 255)
            brightness = data.get("brightness", 100)

            if not device_id:
                return web.json_response(
                    {"success": False, "error": "缺少 device_id 参数"},
                    status=400
                )

            # 限制范围
            red = max(0, min(255, red))
            green = max(0, min(255, green))
            blue = max(0, min(255, blue))
            brightness = max(0, min(100, brightness))

            command = {
                "name": "LED",
                "method": "SetColor",
                "parameters": {
                    "red": red,
                    "green": green,
                    "blue": blue,
                    "brightness": brightness
                }
            }

            result = await self._send_iot_command(device_id, command)
            result["message"] = f"LED 颜色已设置为 RGB({red},{green},{blue})" if result["success"] else result.get("error")

            response = web.json_response(result)
            self._add_cors_headers(response)
            return response

        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "无效的 JSON 数据"},
                status=400
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LED 颜色设置出错: {e}")
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500
            )
