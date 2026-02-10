import json
import platform
from pathlib import Path

# Skill metadata
SKILL_METADATA = {
    "name": "auto_fix",
    "description": "自动检测并修复后端服务（数据库、缓存、消息队列、搜索引擎）的协同配置问题",
    "version": "1.0.0",
    "author": "AI Assistant",
    "commands": [
        {
            "name": "auto_fix",
            "description": "检测并自动修复后端服务问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "指定要检测的服务 (mysql, postgres, mongodb, redis, rabbitmq, kafka, elasticsearch, all)",
                        "enum": ["mysql", "postgres", "mongodb", "redis", "rabbitmq", "kafka", "elasticsearch", "all"],
                        "default": "all"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "只检测不修复",
                        "default": false
                    },
                    "force": {
                        "type": "boolean",
                        "description": "强制执行修复（跳过确认）",
                        "default": false
                    }
                },
                "required": []
            }
        }
    ]
}


def get_system_info():
    """获取当前系统信息"""
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version()
    }


def get_service_default_port(service_name: str) -> int | None:
    """获取服务的默认端口"""
    default_ports = {
        "mysql": 3306,
        "postgres": 5432,
        "mongodb": 27017,
        "redis": 6379,
        "rabbitmq": 5672,
        "kafka": 9092,
        "elasticsearch": 9200
    }
    return default_ports.get(service_name.lower())
