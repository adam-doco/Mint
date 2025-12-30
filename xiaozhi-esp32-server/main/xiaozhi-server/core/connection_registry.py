"""
全局连接注册表
用于跟踪和管理所有活跃的设备 WebSocket 连接
"""

import threading
from typing import Dict, Optional, Any
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class ConnectionRegistry:
    """
    单例模式的连接注册表
    用于在 HTTP API 中查找设备的 WebSocket 连接
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._connections: Dict[str, Any] = {}
                    cls._instance._registry_lock = threading.Lock()
        return cls._instance

    def register(self, device_id: str, connection_handler) -> None:
        """
        注册设备连接

        Args:
            device_id: 设备ID
            connection_handler: ConnectionHandler 实例
        """
        with self._registry_lock:
            self._connections[device_id] = connection_handler
            logger.bind(tag=TAG).info(f"设备已注册: {device_id}")

    def unregister(self, device_id: str) -> None:
        """
        注销设备连接

        Args:
            device_id: 设备ID
        """
        with self._registry_lock:
            if device_id in self._connections:
                del self._connections[device_id]
                logger.bind(tag=TAG).info(f"设备已注销: {device_id}")

    def get_connection(self, device_id: str) -> Optional[Any]:
        """
        获取设备的连接处理器

        Args:
            device_id: 设备ID

        Returns:
            ConnectionHandler 实例，如果不存在则返回 None
        """
        with self._registry_lock:
            return self._connections.get(device_id)

    def get_all_device_ids(self) -> list:
        """
        获取所有已连接的设备ID

        Returns:
            设备ID列表
        """
        with self._registry_lock:
            return list(self._connections.keys())

    def is_connected(self, device_id: str) -> bool:
        """
        检查设备是否已连接

        Args:
            device_id: 设备ID

        Returns:
            是否已连接
        """
        with self._registry_lock:
            return device_id in self._connections


# 全局单例实例
connection_registry = ConnectionRegistry()
