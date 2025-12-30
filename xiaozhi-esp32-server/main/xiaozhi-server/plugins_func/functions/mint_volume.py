"""
米特(Mint) 音量控制插件
让 AI 可以控制米特的音量
"""

import json
import asyncio
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


mint_volume_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_volume",
        "description": (
            "控制米特的音量大小。可以设置具体音量值，或者调大、调小音量。"
            "当用户要求调整音量时使用，例如：'把音量调大一点'、'音量调到50'、'声音太大了'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "音量操作类型",
                    "enum": ["set", "up", "down", "mute", "unmute"],
                },
                "value": {
                    "type": "integer",
                    "description": "音量值(0-100)，仅当action为set时需要",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["action"],
        },
    },
}


@register_function("mint_volume", mint_volume_function_desc, ToolType.IOT_CTL)
def mint_volume(conn, action: str = "set", value: int = 50):
    """
    控制米特的音量

    Args:
        conn: 连接对象
        action: 操作类型 (set/up/down/mute/unmute)
        value: 音量值 (0-100)
    """
    try:
        # 构建 IoT 控制命令
        command = {
            "name": "Speaker",
            "method": "",
            "parameters": {}
        }

        response_text = ""

        if action == "set":
            # 限制音量范围
            value = max(0, min(100, value))
            command["method"] = "SetVolume"
            command["parameters"]["volume"] = value
            response_text = f"好的，音量已调整到 {value}"

        elif action == "up":
            command["method"] = "VolumeUp"
            response_text = "好的，音量已调大"

        elif action == "down":
            command["method"] = "VolumeDown"
            response_text = "好的，音量已调小"

        elif action == "mute":
            command["method"] = "Mute"
            response_text = "好的，已静音"

        elif action == "unmute":
            command["method"] = "Unmute"
            response_text = "好的，已取消静音"

        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                f"不支持的音量操作：{action}"
            )

        # 发送 IoT 命令到 ESP32
        if hasattr(conn, 'websocket') and conn.websocket:
            send_message = json.dumps({
                "type": "iot",
                "commands": [command]
            })

            asyncio.create_task(_send_command(conn.websocket, send_message))
            logger.bind(tag=TAG).info(f"音量控制命令已发送: {command}")

            return ActionResponse(
                Action.RESPONSE,
                None,
                response_text
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，设备连接不可用"
            )

    except Exception as e:
        logger.bind(tag=TAG).error(f"音量控制出错: {e}")
        return ActionResponse(
            Action.ERROR,
            str(e),
            "调整音量时出错了"
        )


async def _send_command(websocket, message):
    """异步发送命令"""
    try:
        await websocket.send(message)
    except Exception as e:
        logger.bind(tag=TAG).error(f"发送命令失败: {e}")


# 额外提供一个查询音量的函数
mint_get_volume_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_get_volume",
        "description": (
            "查询米特当前的音量大小。"
            "当用户询问当前音量时使用，例如：'现在音量是多少？'、'音量多大？'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


@register_function("mint_get_volume", mint_get_volume_function_desc, ToolType.IOT_CTL)
def mint_get_volume(conn):
    """
    查询米特当前的音量

    Args:
        conn: 连接对象
    """
    try:
        # 从 IoT 描述符中获取音量状态
        if hasattr(conn, 'iot_descriptors') and conn.iot_descriptors:
            for key, descriptor in conn.iot_descriptors.items():
                if key.lower() == "speaker":
                    for prop in descriptor.properties:
                        if prop["name"].lower() == "volume":
                            volume = prop.get("value", "未知")
                            return ActionResponse(
                                Action.RESPONSE,
                                None,
                                f"当前音量是 {volume}"
                            )

        # 如果没有找到，返回默认信息
        return ActionResponse(
            Action.RESPONSE,
            None,
            "抱歉，无法获取当前音量"
        )

    except Exception as e:
        logger.bind(tag=TAG).error(f"查询音量出错: {e}")
        return ActionResponse(
            Action.ERROR,
            str(e),
            "查询音量时出错了"
        )
