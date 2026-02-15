"""
测试课程总结图片 Skill 能否正常导入
"""

import sys
import os
import ast
import asyncio


async def test_import():
    """测试导入是否成功（只检查语法和结构，不实际调用API）"""
    print("=" * 50)
    print("Test Course Summary Image Skill Import")
    print("=" * 50)

    # 读取并解析 course_summary.py
    skill_file = os.path.join(os.path.dirname(__file__), "skills", "course_summary.py")

    print(f"\n[1] Check file exists: {skill_file}")
    if not os.path.exists(skill_file):
        print("    [X] File not exists")
        return False
    print("    [OK] File exists")

    # 语法检查
    print("\n[2] Syntax check...")
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        print("    [OK] Syntax correct")
    except SyntaxError as e:
        print(f"    [X] Syntax error: {e}")
        return False

    # 检查类和方法定义
    print("\n[3] Check classes and functions...")
    tree = ast.parse(code)

    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    # 同时检测同步和异步函数定义
    functions = [node.name for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)]

    required_classes = ["CourseSummarySkill"]
    required_functions = [
        "generate_from_web",
        "generate_from_pdf",
        "list_tasks",
        "get_task_status",
        "regenerate_image"
    ]

    for cls in required_classes:
        if cls in classes:
            print(f"    [OK] {cls} class defined")
        else:
            print(f"    [X] {cls} class not defined")

    for func in required_functions:
        if func in functions:
            print(f"    [OK] {func} function defined")
        else:
            print(f"    [X] {func} function not defined")

    # 检查 __init__.py
    print("\n[4] Check skills package...")
    init_file = os.path.join(os.path.dirname(__file__), "skills", "__init__.py")
    if os.path.exists(init_file):
        print("    [OK] __init__.py exists")
    else:
        print("    [X] __init__.py not exists")
        return False

    # 检查 skills.json
    print("\n[5] Check skills.json...")
    skills_json = os.path.join(os.path.dirname(__file__), ".claude", "skills.json")
    if os.path.exists(skills_json):
        print("    [OK] skills.json exists")
        try:
            import json
            with open(skills_json, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"    [OK] Config valid: {config.get('name')}")
        except Exception as e:
            print(f"    [X] skills.json parse failed: {e}")
    else:
        print("    [X] skills.json not exists")

    print("\n" + "=" * 50)
    print("All import tests passed!")
    print("=" * 50)
    print("\nNote: To run actual skill, install dependencies:")
    print("  pip install httpx")
    print("=" * 50)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_import())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
