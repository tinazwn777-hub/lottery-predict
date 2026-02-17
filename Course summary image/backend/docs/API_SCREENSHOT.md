# API 截图服务配置

## 支持的后端

### 1. hcti.io (htmlcsstoimage)
- **网站**: https://hcti.io
- **免费额度**: 100 张图片/月
- **价格**: $9/月 起

### 2. APIFlash
- **网站**: https://apiflash.com
- **免费额度**: 100 张图片/月
- **价格**: $15/月 起

## 配置方法

### 方法一：环境变量

```bash
# hcti.io 配置
export HCTI_API_KEY="your_api_key"
export HCTI_API_ID="your_api_id"

# 或者 APIFlash 配置
export APIFLASH_API_KEY="your_api_key"
```

### 方法二：.env 文件

在 `backend/.env` 文件中添加：

```env
# hcti.io
HCTI_API_KEY=your_api_key
HCTI_API_ID=your_api_id

# 或者
APIFLASH_API_KEY=your_api_key
```

### 方法三：代码中设置

```python
from app.services.image.api_screenshot import HtmlCssToImageAPI

api = HtmlCssToImageAPI(
    api_key="your_api_key",
    api_id="your_api_id"
)
```

## 快速开始

### 1. 注册 hcti.io

1. 访问 https://hcti.io
2. 注册账号
3. 获取 API Key 和 API ID
4. 配置到环境变量或 .env 文件

### 2. 测试

```bash
# 运行测试
python test_api_screenshot.py
```

## 备用方案

如果 API 不可用，会自动回退到本地渲染（需要安装 html2image 和 pygame）。

```bash
pip install html2image pygame
```

## 价格对比

| 服务 | 免费额度 | 价格 |
|------|---------|------|
| hcti.io | 100 张/月 | $9/月 |
| APIFlash | 100 张/月 | $15/月 |
| ScreenshotAPI | 100 张/月 | $10/月 |

## 自定义后端

可以轻松添加新的渲染后端：

```python
from app.services.image.api_screenshot import BaseScreenshotAPI

class MyCustomAPI(BaseScreenshotAPI):
    def generate(self, html: str, output_path: str) -> str:
        # 实现你的渲染逻辑
        pass

# 使用自定义后端
from app.services.image.api_screenshot import ScreenshotAPIService

class CustomService(ScreenshotAPIService):
    BACKENDS = {
        "custom": MyCustomAPI,
    }

service = ScreenshotAPIService("custom")
```
