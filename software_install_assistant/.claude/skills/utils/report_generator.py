"""
报告生成

生成格式化的诊断报告。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        pass

    def generate_health_report(
        self,
        health_checks: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成健康检查报告"""
        all_healthy = all(
            result.get("is_healthy", False)
            for result in health_checks.values()
        )

        return {
            "type": "health_check_report",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": len(health_checks),
                "healthy_count": sum(1 for r in health_checks.values() if r.get("is_healthy", False)),
                "all_healthy": all_healthy
            },
            "services": health_checks
        }

    def generate_issue_report(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成问题报告"""
        # 按严重程度分组
        severity_groups = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for issue in issues:
            severity = issue.get("severity", "medium")
            if severity not in severity_groups:
                severity = "medium"
            severity_groups[severity].append(issue)

        return {
            "type": "issue_report",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_issues": len(issues),
                "critical_count": len(severity_groups["critical"]),
                "high_count": len(severity_groups["high"]),
                "medium_count": len(severity_groups["medium"]),
                "low_count": len(severity_groups["low"])
            },
            "issues_by_severity": severity_groups,
            "all_issues": issues
        }

    def generate_fix_report(
        self,
        fixes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成修复报告"""
        success_count = sum(1 for f in fixes if f.get("fix_result", {}).get("success", False))

        return {
            "type": "fix_report",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_fixes": len(fixes),
                "success_count": success_count,
                "failure_count": len(fixes) - success_count
            },
            "fixes": fixes
        }

    def generate_complete_report(
        self,
        health_checks: Dict[str, Dict[str, Any]],
        issues: List[Dict[str, Any]],
        fixes: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成完整报告"""
        success_count = sum(1 for f in fixes if f.get("fix_result", {}).get("success", False))

        return {
            "type": "complete_report",
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "summary": {
                "services_checked": len(health_checks),
                "services_healthy": sum(1 for r in health_checks.values() if r.get("is_healthy", False)),
                "issues_detected": len(issues),
                "issues_fixed": success_count,
                "fix_success_rate": round(success_count / len(fixes) * 100, 1) if fixes else 100
            },
            "health_checks": health_checks,
            "issues": issues,
            "fixes": fixes
        }

    def format_report_text(
        self,
        report: Dict[str, Any],
        format_type: str = "markdown"
    ) -> str:
        """格式化报告为文本

        Args:
            report: 报告字典
            format_type: 输出格式 (markdown, plain, json)

        Returns:
            格式化的报告文本
        """
        if format_type == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)
        elif format_type == "markdown":
            return self._format_markdown(report)
        else:
            return self._format_plain(report)

    def _format_markdown(self, report: Dict[str, Any]) -> str:
        """格式化为 Markdown"""
        lines = []

        report_type = report.get("type", "report")

        if report_type == "complete_report":
            lines.append("# 服务诊断修复报告")
            lines.append("")
            lines.append(f"**生成时间**: {report.get('timestamp', '')}")
            lines.append("")

            summary = report.get("summary", {})
            lines.append("## 汇总")
            lines.append(f"- 检查服务数: {summary.get('services_checked', 0)}")
            lines.append(f"- 健康服务数: {summary.get('services_healthy', 0)}")
            lines.append(f"- 发现问题数: {summary.get('issues_detected', 0)}")
            lines.append(f"- 修复成功数: {summary.get('issues_fixed', 0)}")
            lines.append("")

            # 健康检查结果
            lines.append("## 健康检查")
            health_checks = report.get("health_checks", {})
            for service, result in health_checks.items():
                status = "✓" if result.get("is_healthy") else "✗"
                lines.append(f"- {status} **{service}**: {result.get('message', '')}")
            lines.append("")

            # 问题列表
            issues = report.get("issues", [])
            if issues:
                lines.append("## 发现的问题")
                for i, issue in enumerate(issues, 1):
                    lines.append(f"### {i}. {issue.get('title', '')}")
                    lines.append(f"- **严重程度**: {issue.get('severity', '')}")
                    lines.append(f"- **描述**: {issue.get('description', '')}")
                    lines.append(f"- **建议**: {issue.get('suggestion', '')}")
                    lines.append("")

            # 修复结果
            fixes = report.get("fixes", [])
            if fixes:
                lines.append("## 修复结果")
                for fix in fixes:
                    issue_title = fix.get("issue", {}).get("title", '')
                    result = fix.get("fix_result", {})
                    status = "✓" if result.get("success") else "✗"
                    lines.append(f"- {status} **{issue_title}**: {result.get('message', '')}")
                    if result.get("changes"):
                        lines.append(f"  - 变更: {', '.join(result.get('changes', []))}")

        elif report_type == "issue_report":
            lines.append("# 问题报告")
            lines.append("")
            summary = report.get("summary", {})
            lines.append("## 汇总")
            lines.append(f"- 发现问题总数: {summary.get('total_issues', 0)}")

            issues = report.get("all_issues", [])
            for i, issue in enumerate(issues, 1):
                lines.append(f"\n### {i}. {issue.get('title', '')}")
                lines.append(f"- **类型**: {issue.get('issue_type', '')}")
                lines.append(f"- **严重程度**: {issue.get('severity', '')}")
                lines.append(f"- **描述**: {issue.get('description', '')}")
                lines.append(f"- **建议**: {issue.get('suggestion', '')}")

        else:
            # 默认格式
            lines.append(json.dumps(report, indent=2, ensure_ascii=False))

        return '\n'.join(lines)

    def _format_plain(self, report: Dict[str, Any]) -> str:
        """格式化为纯文本"""
        lines = []

        report_type = report.get("type", "report")

        if report_type == "complete_report":
            summary = report.get("summary", {})
            lines.append("=" * 50)
            lines.append("服务诊断修复报告")
            lines.append("=" * 50)
            lines.append(f"检查服务: {summary.get('services_checked', 0)}")
            lines.append(f"健康服务: {summary.get('services_healthy', 0)}")
            lines.append(f"发现问题: {summary.get('issues_detected', 0)}")
            lines.append(f"修复成功: {summary.get('issues_fixed', 0)}")
            lines.append("-" * 50)

            # 健康检查
            health_checks = report.get("health_checks", {})
            for service, result in health_checks.items():
                status = "[OK]" if result.get("is_healthy") else "[FAIL]"
                lines.append(f"{status} {service}: {result.get('message', '')}")

            # 问题
            issues = report.get("issues", [])
            if issues:
                lines.append("\n发现问题:")
                for issue in issues:
                    lines.append(f"  - [{issue.get('severity', '').upper()}] {issue.get('title', '')}")
                    lines.append(f"    {issue.get('description', '')}")
                    lines.append(f"    建议: {issue.get('suggestion', '')}")

            lines.append("=" * 50)

        else:
            lines.append(json.dumps(report, indent=2, ensure_ascii=False))

        return '\n'.join(lines)

    def save_report(
        self,
        report: Dict[str, Any],
        file_path: str,
        format_type: str = "json"
    ) -> bool:
        """保存报告到文件

        Args:
            report: 报告字典
            file_path: 输出文件路径
            format_type: 输出格式 (json, markdown, plain)

        Returns:
            是否保存成功
        """
        try:
            content = self.format_report_text(report, format_type)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception:
            return False
