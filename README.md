# 校园失物招领智能匹配系统

## 项目简介

这是一个基于 Flask 的校园失物招领智能匹配系统，融合了深度学习和自然语言处理技术，通过多维度智能匹配算法，帮助用户快速找到丢失物品或归还拾获物品。

## 技术亮点（近5年技术）

### 1. 深度学习图像识别
- **技术**：PyTorch + ResNet18 预训练模型
- **功能**：自动提取图像深度特征，实现物品图片的智能比对
- **优势**：相比传统哈希算法，能识别相似物品的不同角度/光照图片

### 2. 语义相似度匹配
- **技术**：Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **功能**：基于BERT的多语言语义理解，计算文本描述相似度
- **优势**：支持中英文混合，理解语义而非简单关键词匹配

### 3. 数据可视化仪表盘
- **技术**：ECharts 5.4 + 异步数据加载
- **功能**：实时展示系统运营数据、趋势分析、热力图
- **优势**：直观的数据展示，支持多维度统计分析

### 4. WebSocket 实时推送
- **技术**：Flask-SocketIO + WebSocket 协议
- **功能**：匹配结果实时推送，无需刷新页面
- **优势**：即时通知，提升用户体验

### 5. RESTful API 接口
- **技术**：Flask-RESTful + JWT 认证
- **功能**：提供标准化API，支持移动端接入
- **优势**：前后端分离架构，易于扩展

## 主要功能

| 功能模块 | 说明 |
|---------|------|
| 用户系统 | 注册、登录、个人信息管理 |
| 丢失物品发布 | 发布丢失物品信息，上传图片 |
| 拾获物品发布 | 发布拾获物品信息，上传图片 |
| 智能匹配 | 深度学习+语义分析多维度匹配 |
| 匹配管理 | 查看、确认、忽略匹配结果 |
| 数据仪表盘 | 可视化统计分析 |
| RESTful API | 移动端接口支持 |

## 技术栈

| 类别 | 技术 |
|-----|------|
| 后端框架 | Flask 3.0 |
| 数据库 | SQLite / MySQL |
| 深度学习 | PyTorch 2.1 + torchvision |
| NLP | transformers + sentence-transformers |
| 实时通信 | Flask-SocketIO (WebSocket) |
| 前端 | Bootstrap 5 + ECharts 5.4 |
| 图像处理 | Pillow + imagehash |

## 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装步骤

1. **Windows 用户**：双击运行 `start.bat`

2. **手动安装**：
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖（使用国内镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行项目
python run.py
```

3. 访问 http://localhost:5000

## 项目结构

```
lost-found-system/
├── app/
│   ├── __init__.py              # 应用初始化
│   ├── models/models.py         # 数据模型
│   ├── forms/forms.py           # 表单验证
│   ├── routes/
│   │   ├── auth.py              # 认证路由
│   │   ├── main.py              # 主页路由
│   │   ├── lost.py              # 丢失物品
│   │   ├── found.py             # 拾获物品
│   │   ├── match.py             # 匹配管理
│   │   ├── dashboard.py         # 数据仪表盘
│   │   └── api.py               # RESTful API
│   ├── utils/
│   │   ├── matcher.py           # 智能匹配引擎
│   │   ├── image_classifier.py  # 深度学习图像识别
│   │   ├── semantic_matcher.py  # 语义相似度匹配
│   │   └── notifications.py     # 实时通知
│   └── templates/               # 前端模板
├── static/uploads/              # 上传文件目录
├── requirements.txt             # 依赖列表
├── run.py                       # 启动文件
└── start.bat                    # Windows启动脚本
```

## 智能匹配算法

系统采用多维度融合匹配策略：

| 维度 | 权重 | 技术方案 |
|-----|------|---------|
| 深度图像特征 | 35% | ResNet18 特征提取 + 余弦相似度 |
| 语义文本相似度 | 30% | Sentence-Transformers 语义编码 |
| 感知哈希 | 20% | pHash 图像指纹 |
| 类别匹配 | 15% | 精确匹配 |

当综合相似度 >= 60% 时，自动生成匹配记录。

## API 接口

| 接口 | 方法 | 说明 |
|-----|------|------|
| /api/search | GET | 搜索物品 |
| /api/categories | GET | 获取分类列表 |
| /api/lost | GET | 丢失物品列表 |
| /api/found | GET | 拾获物品列表 |
| /api/match/<lost_id>/<found_id> | GET | 匹配详情 |
| /api/recommend/<item_id> | GET | 推荐匹配 |
| /api/stats | GET | 统计数据 |

## 使用说明

1. **注册账号**：填写用户名、邮箱、密码
2. **发布丢失物品**：点击"我丢了东西"，填写物品信息
3. **发布拾获物品**：点击"我捡到东西"，填写物品信息
4. **查看匹配**：系统自动匹配，在"匹配结果"页面查看
5. **确认匹配**：找到正确匹配后点击确认
6. **数据仪表盘**：查看系统运营数据和统计图表

## 开发者

毕业设计作品 - 2024

## 技术创新点

1. **多模态融合匹配**：结合图像深度特征和文本语义特征，提高匹配准确率
2. **预训练模型应用**：利用ImageNet预训练的ResNet18，无需大量训练数据
3. **多语言语义理解**：支持中英文混合描述的语义匹配
4. **实时推送架构**：基于WebSocket的即时通知机制
5. **渐进式功能设计**：支持基础模式和高级模式，灵活部署
