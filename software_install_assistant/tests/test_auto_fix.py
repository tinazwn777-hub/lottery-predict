"""
测试模块
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# 测试夹子
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 测试用例
class TestBaseAdapter:
    """测试适配器基类"""

    def test_issue_type_enum(self):
        """测试问题类型枚举"""
        from .claude.skills.base.base_adapter import IssueType

        assert IssueType.SERVICE_NOT_RUNNING.value == 1
        assert IssueType.PORT_NOT_LISTENING.value == 2
        assert IssueType.CONFIG_INVALID.value == 4

    def test_health_result_creation(self):
        """测试健康检查结果创建"""
        from .claude.skills.base.base_adapter import HealthResult

        result = HealthResult(
            service_name="test",
            is_healthy=True,
            message="Test passed",
            details={"key": "value"}
        )

        assert result.service_name == "test"
        assert result.is_healthy is True
        assert result.details["key"] == "value"

    def test_health_result_to_dict(self):
        """测试健康检查结果序列化"""
        from .claude.skills.base.base_adapter import HealthResult

        result = HealthResult(
            service_name="test",
            is_healthy=True,
            message="OK"
        )

        data = result.to_dict()
        assert data["service_name"] == "test"
        assert data["is_healthy"] is True


class TestDatabaseAdapter:
    """测试数据库适配器"""

    @pytest.fixture
    def adapter(self):
        """创建数据库适配器实例"""
        from .claude.skills.services.database import DatabaseAdapter
        return DatabaseAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.SERVICE_NAME == "database"
        assert len(adapter.databases) == 3

    def test_get_sub_services(self, adapter):
        """测试获取子服务"""
        sub_services = adapter.get_sub_services()
        assert "mysql" in sub_services
        assert "postgres" in sub_services
        assert "mongodb" in sub_services


class TestRedisAdapter:
    """测试 Redis 适配器"""

    @pytest.fixture
    def adapter(self):
        """创建 Redis 适配器实例"""
        from .claude.skills.services.redis import RedisAdapter
        return RedisAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.SERVICE_NAME == "redis"
        assert 6379 in adapter.DEFAULT_PORTS

    def test_config_paths(self, adapter):
        """测试配置文件路径"""
        paths = adapter.CONFIG_PATHS
        assert len(paths) > 0


class TestMessageQueueAdapter:
    """测试消息队列适配器"""

    @pytest.fixture
    def adapter(self):
        """创建消息队列适配器实例"""
        from .claude.skills.services.message_queue import MessageQueueAdapter
        return MessageQueueAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.SERVICE_NAME == "message_queue"

    def test_get_sub_services(self, adapter):
        """测试获取子服务"""
        sub_services = adapter.get_sub_services()
        assert "rabbitmq" in sub_services
        assert "kafka" in sub_services


class TestElasticsearchAdapter:
    """测试 Elasticsearch 适配器"""

    @pytest.fixture
    def adapter(self):
        """创建 Elasticsearch 适配器实例"""
        from .claude.skills.services.elasticsearch import ElasticsearchAdapter
        return ElasticsearchAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.SERVICE_NAME == "elasticsearch"
        assert 9200 in adapter.DEFAULT_PORTS


class TestHealthChecker:
    """测试健康检查工具"""

    def test_parse_ini_config(self):
        """测试 INI 配置解析"""
        from .claude.skills.base.health_checker import HealthChecker

        content = """
[section1]
key1=value1
key2=value2

[section2]
key3=value3
"""
        config = HealthChecker.parse_ini_config(content)

        assert "section1" in config
        assert config["section1"]["key1"] == "value1"

    def test_parse_env_config(self):
        """测试 env 配置解析"""
        from .claude.skills.base.health_checker import HealthChecker

        content = """
# 这是注释
KEY1=value1
KEY2="quoted value"
KEY3='single quoted'
"""
        config = HealthChecker.parse_env_config(content)

        assert config["KEY1"] == "value1"
        assert config["KEY2"] == "quoted value"

    def test_parse_json_config(self):
        """测试 JSON 配置解析"""
        from .claude.skills.base.health_checker import HealthChecker

        content = '{"key": "value", "number": 42}'
        config = HealthChecker.parse_json_config(content)

        assert config["key"] == "value"
        assert config["number"] == 42


class TestConfigParser:
    """测试配置解析器"""

    @pytest.fixture
    def parser(self):
        """创建配置解析器"""
        from .claude.skills.utils.config_parser import ConfigParser
        return ConfigParser()

    def test_parse_json(self, parser):
        """测试 JSON 解析"""
        config = parser.parse_json('{"key": "value"}')
        assert config["key"] == "value"

    def test_parse_kv(self, parser):
        """测试 KV 格式解析"""
        config = parser._parse_kv("KEY=value\nKEY2=value2")
        assert config["KEY"] == "value"

    def test_get_value(self, parser):
        """测试获取嵌套值"""
        data = {
            "database": {
                "host": "localhost",
                "port": 3306
            }
        }

        assert parser.get_value(data, "database.host") == "localhost"
        assert parser.get_value(data, "database.port") == 3306
        assert parser.get_value(data, "database.nonexistent", "default") == "default"


class TestReportGenerator:
    """测试报告生成器"""

    @pytest.fixture
    def generator(self):
        """创建报告生成器"""
        from .claude.skills.utils.report_generator import ReportGenerator
        return ReportGenerator()

    def test_generate_health_report(self, generator):
        """测试健康报告生成"""
        health_checks = {
            "mysql": {"is_healthy": True, "message": "OK"},
            "redis": {"is_healthy": False, "message": "Failed"}
        }

        report = generator.generate_health_report(health_checks)

        assert report["type"] == "health_check_report"
        assert report["summary"]["total_services"] == 2
        assert report["summary"]["healthy_count"] == 1

    def test_format_markdown(self, generator):
        """测试 Markdown 格式化"""
        report = {
            "type": "complete_report",
            "timestamp": "2024-01-01T00:00:00",
            "summary": {
                "services_checked": 2,
                "services_healthy": 1,
                "issues_detected": 1,
                "issues_fixed": 1
            },
            "health_checks": {
                "mysql": {"is_healthy": True, "message": "OK"}
            },
            "issues": [],
            "fixes": []
        }

        markdown = generator.format_report_text(report, "markdown")

        assert "# 服务诊断修复报告" in markdown
        assert "mysql" in markdown


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
