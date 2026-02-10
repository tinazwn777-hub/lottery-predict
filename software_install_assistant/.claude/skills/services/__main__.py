#!/usr/bin/env python3
"""
OCR Service 快速测试
"""

import sys
sys.path.insert(0, '.')

from .claude.skills.services.ocr import OcrService, ErrorCategory


def print_ocr_result(result):
    """打印 OCR 识别结果"""
    print("\n" + "=" * 50)
    print("OCR 识别结果")
    print("=" * 50)

    if result["success"]:
        print(f"识别状态: 成功")
        print(f"置信度: {result['confidence']:.2%}")
        print(f"\n识别文字:")
        print("-" * 50)
        print(result["recognized_text"][:500] if len(result["recognized_text"]) > 500 else result["recognized_text"])
        print("-" * 50)

        if result["error_categories"]:
            print(f"\n错误类别: {', '.join(result['error_categories'])}")

        if result["keywords"]:
            print(f"关键词: {', '.join(result['keywords'])}")

        if result["suggested_actions"]:
            print(f"\n建议操作:")
            for i, action in enumerate(result["suggested_actions"], 1):
                print(f"  {i}. {action}")
    else:
        print(f"识别状态: 失败")
        print(f"错误信息: {result.get('error_details', result.get('error', '未知错误'))}")
        if result.get('suggested_actions'):
            print(f"\n建议:")
            for action in result['suggested_actions']:
                print(f"  - {action}")


def main():
    """主函数"""
    print("初始化 OCR 服务...")

    service = OcrService()

    print(f"Tesseract 可用: {service.available}")
    if service.available:
        print(f"Tesseract 版本: {service.version}")

    if len(sys.argv) > 1:
        # 从命令行参数读取图片路径
        image_path = sys.argv[1]
        print(f"\n识别图片: {image_path}")

        result = service.analyze_screenshot(image_path)
        print_ocr_result(result)
    else:
        # 显示使用说明
        print("\n" + "=" * 50)
        print("使用说明")
        print("=" * 50)
        print("""
# 识别图片中的错误信息
python -m .claude.skills.services.ocr <图片路径>

# 使用示例
python -m .claude.skills.services.ocr ./error_screenshot.png

# 识别 Base64 图片
python -c "
from .claude.skills.services.ocr import recognize_base64_error
import base64
with open('test.png', 'rb') as f:
    result = recognize_base64_error(base64.b64encode(f.read()).decode())
    print(result)
"
        """)

        # 测试示例
        print("\n" + "=" * 50)
        print("支持的错误类别")
        print("=" * 50)
        for category in ErrorCategory:
            print(f"  - {category.name}")


if __name__ == "__main__":
    main()
