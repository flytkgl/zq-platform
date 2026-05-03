# ZQ Platform - FastAPI Backend

基于 FastAPI 的现代化异步后端服务，使用 SQLAlchemy 异步 ORM + Alembic 数据库迁移 + PostgreSQL。

## 技术栈

- **框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 16+
- **ORM**: SQLAlchemy 2.0+ (异步)
- **迁移**: Alembic
- **认证**: JWT
- **缓存**: Redis
- **Python**: 3.12+

## 项目结构

```
backend-fastapi/
├── app/                      # 核心应用模块
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── base_model.py        # BaseModel 基类
│   ├── base_schema.py       # 通用 Schema
│   ├── base_service.py      # BaseService 基类
│   ├── redis.py             # Redis 缓存
│   └── excel.py             # Excel 工具
├── core/                     # 核心业务模块
│   ├── user/                # 用户管理
│   ├── role/                # 角色管理
│   ├── menu/                # 菜单管理
│   ├── dept/                # 部门管理
│   ├── permission/          # 权限管理
│   └── ...
├── scheduler/               # 定时任务模块
│   ├── model.py
│   ├── service.py
│   └── tasks.py
├── zq_demo/                 # 示例模块
│   ├── demo/
│   └── demo_cache/
├── scripts/                 # 工具脚本
│   ├── dumpdata.py         # 数据导出
│   └── loaddata.py         # 数据导入
├── alembic/                 # 数据库迁移
│   ├── versions/
│   └── env.py
├── env/                     # 环境配置
│   ├── dev.env
│   ├── uat.env
│   └── prod.env
├── main.py                  # 应用入口
├── requirements.txt         # 依赖列表
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n zq-fastapi python=3.12
conda activate zq-fastapi

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境配置文件：

```bash
cp env/example.env env/dev.env
```

编辑 `env/dev.env`，配置数据库连接：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. 数据库迁移

```bash
# 首次使用：生成初始迁移
alembic revision --autogenerate -m "init tables"

# 执行迁移
alembic upgrade head

# 导入数据
python scripts/loaddata.py db_init.json
```

### 5. 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 数据库操作

### 迁移命令

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 生成新的迁移文件
alembic revision --autogenerate -m "描述信息"

# 升级到最新版本
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

### 数据导入导出

#### 导出数据（dumpdata.py）

```bash
# 导出所有数据到文件
python scripts/dumpdata.py -o db_init.json -f

# 导出指定模块（如 core）
python scripts/dumpdata.py core -o core_data.json -f

# 导出到标准输出（不指定 -o 参数）
python scripts/dumpdata.py > data.json

# 导出指定模块到标准输出
python scripts/dumpdata.py core > core_data.json
```

**参数说明：**

- `app_name`（位置参数，可选）：指定要导出的应用/模块名称
  - 例如：`core`、`scheduler`、`zq_demo`
  - 不指定则导出所有数据
  
- `-o, --output`：指定输出文件路径
  - 例如：`-o db_init.json`
  - 不指定则输出到标准输出（stdout）
  
- `-f, --force`：强制覆盖已存在的文件
  - 如果输出文件已存在且未使用此参数，脚本会报错并退出
  - 使用此参数可以强制覆盖现有文件

**示例：**

```bash
# 导出所有数据，如果文件存在则覆盖
python scripts/dumpdata.py -o db_init.json -f

# 导出 core 模块数据，不覆盖已存在文件（文件存在会报错）
python scripts/dumpdata.py core -o core_data.json

# 导出 scheduler 模块数据到标准输出，然后重定向到文件
python scripts/dumpdata.py scheduler > scheduler_data.json
```

#### 导入数据（loaddata.py）

```bash
# 导入数据
python scripts/loaddata.py db_init.json

# 导入多个文件
python scripts/loaddata.py core_data.json scheduler_data.json
```

**参数说明：**

- `files`（位置参数，必需）：要导入的 JSON 文件路径，可以指定多个文件

## 开发指南

### 新建模块

按照以下步骤创建新的业务模块（以 `example` 为例）：

#### 1. 创建模块目录

```bash
mkdir -p core/example
touch core/example/__init__.py
touch core/example/model.py
touch core/example/schema.py
touch core/example/service.py
touch core/example/api.py
```

#### 2. 定义模型 (model.py)

```python
from sqlalchemy import Column, String, Boolean
from app.base_model import BaseModel

class Example(BaseModel):
    __tablename__ = "core_example"
    
    name = Column(String(100), nullable=False, comment="名称")
    description = Column(String(500), comment="描述")
    is_active = Column(Boolean, default=True, comment="是否激活")
```

#### 3. 定义 Schema (schema.py)

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ExampleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ExampleResponse(ExampleBase):
    id: str
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[datetime] = None
    sys_update_datetime: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
```

#### 4. 定义服务 (service.py)

```python
from app.base_service import BaseService
from core.example.model import Example
from core.example.schema import ExampleCreate, ExampleUpdate

class ExampleService(BaseService[Example, ExampleCreate, ExampleUpdate]):
    model = Example
```

#### 5. 定义 API (api.py)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from core.example.schema import ExampleCreate, ExampleUpdate, ExampleResponse
from core.example.service import ExampleService

router = APIRouter(prefix="/example", tags=["示例管理"])

@router.post("", response_model=ExampleResponse, summary="创建")
async def create(data: ExampleCreate, db: AsyncSession = Depends(get_db)):
    return await ExampleService.create(db=db, data=data)

@router.get("", response_model=PaginatedResponse[ExampleResponse], summary="获取列表")
async def get_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db)
):
    items, total = await ExampleService.get_list(db, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total)

@router.get("/{record_id}", response_model=ExampleResponse, summary="获取详情")
async def get_by_id(record_id: str, db: AsyncSession = Depends(get_db)):
    result = await ExampleService.get_by_id(db, record_id=record_id)
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    return result

@router.put("/{record_id}", response_model=ExampleResponse, summary="更新")
async def update(record_id: str, data: ExampleUpdate, db: AsyncSession = Depends(get_db)):
    result = await ExampleService.update(db, record_id=record_id, data=data)
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    return result

@router.delete("/{record_id}", response_model=ResponseModel, summary="删除")
async def delete(record_id: str, db: AsyncSession = Depends(get_db)):
    success = await ExampleService.delete(db, record_id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return ResponseModel(message="删除成功")
```

#### 6. 注册路由

在 `core/router.py` 中添加：

```python
from core.example.api import router as example_router

router.include_router(example_router)
```

#### 7. 生成数据库迁移

```bash
alembic revision --autogenerate -m "add example table"
alembic upgrade head
```

## 核心功能

### BaseModel

所有模型继承自 `BaseModel`，自动包含以下字段：

- `id`: UUID 主键
- `sort`: 排序字段
- `is_deleted`: 软删除标记
- `sys_create_datetime`: 创建时间
- `sys_update_datetime`: 更新时间
- `sys_creator_id`: 创建人ID
- `sys_modifier_id`: 修改人ID

### BaseService

提供通用 CRUD 操作：

- `create()`: 创建记录
- `get_by_id()`: 根据ID获取
- `get_list()`: 分页查询
- `update()`: 更新记录
- `delete()`: 删除记录（软删除/硬删除）
- `check_unique()`: 唯一性检查
- `export_to_excel()`: 导出Excel
- `import_from_excel()`: 导入Excel

### 缓存支持

使用 Redis 缓存，继承 `CacheService` 获得缓存功能：

```python
from app.cache_service import CacheService

class ExampleService(CacheService[Example, ExampleCreate, ExampleUpdate]):
    model = Example
    cache_prefix = "example"
    cache_ttl = 3600  # 1小时
```

## 环境配置

项目支持多环境配置：

- `env/dev.env`: 开发环境
- `env/uat.env`: UAT环境
- `env/prod.env`: 生产环境

通过环境变量 `ENV` 切换：

```bash
export ENV=prod  # 使用生产环境配置
python main.py
```

## API 规范

### 响应格式

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

分页响应：

```json
{
  "items": [...],
  "total": 100
}
```

错误响应：

```json
{
  "detail": "错误信息"
}
```

### 路由命名规范

- 使用小写短横线：`/api/core/user-profile`
- 静态路由在前：`/api/core/menu/check/name`
- 动态路由在后：`/api/core/menu/{menu_id}`

## 常见问题

### 1. 迁移文件为空

确保 `alembic/env.py` 中的 `auto_import_models()` 函数正确扫描了所有模型文件。

### 2. 路由重定向 307

检查路由定义，使用 `@router.post("")` 而不是 `@router.post("/")`。

### 3. 数据库连接失败

检查 `env/dev.env` 中的 `DATABASE_URL` 配置是否正确。

# WeasyPrint 安装与配置指南

本文档介绍如何在不同操作系统上安装和配置 WeasyPrint 及其依赖。

## 目录

- [macOS](#macos)
- [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
- [Linux (CentOS/RHEL)](#linux-centosrhel)
- [Windows](#windows)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## macOS

### 1. 安装系统依赖

使用 Homebrew 安装所需的系统库：

```bash
brew install pango glib gobject-introspection harfbuzz cairo fontconfig freetype
```

### 2. 安装 Python 依赖

```bash
pip install weasyprint==62.3
```

### 3. 配置环境变量

WeasyPrint 需要能够找到系统库。将以下内容添加到 `~/.zshrc`（如果使用 bash，则添加到 `~/.bash_profile`）：

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/glib/lib:/opt/homebrew/opt/pango/lib:/opt/homebrew/opt/harfbuzz/lib:/opt/homebrew/opt/cairo/lib:/opt/homebrew/opt/fontconfig/lib:/opt/homebrew/opt/freetype/lib:$DYLD_LIBRARY_PATH"
```

**自动添加方法：**

```bash
echo 'export DYLD_LIBRARY_PATH="/opt/homebrew/opt/glib/lib:/opt/homebrew/opt/pango/lib:/opt/homebrew/opt/harfbuzz/lib:/opt/homebrew/opt/cairo/lib:/opt/homebrew/opt/fontconfig/lib:/opt/homebrew/opt/freetype/lib:$DYLD_LIBRARY_PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 4. 重启终端或 IDE

关闭并重新打开终端窗口，或者重启 IDE，使环境变量生效。

---

## Linux (Ubuntu/Debian)

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libglib2.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libfreetype6
```

### 2. 安装 Python 依赖

```bash
pip install weasyprint==62.3
```

### 3. 配置环境变量（通常不需要）

在 Linux 上，系统库通常已经在标准路径中，不需要额外配置环境变量。

如果遇到库加载问题，可以添加到 `~/.bashrc`：

```bash
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
source ~/.bashrc
```

---

## Linux (CentOS/RHEL)

### 1. 安装系统依赖

```bash
sudo yum install -y \
    pango \
    pango-devel \
    cairo \
    cairo-devel \
    glib2 \
    glib2-devel \
    harfbuzz \
    harfbuzz-devel \
    fontconfig \
    fontconfig-devel \
    freetype \
    freetype-devel \
    libffi-devel
```

或者使用 dnf（CentOS 8+）：

```bash
sudo dnf install -y \
    pango \
    pango-devel \
    cairo \
    cairo-devel \
    glib2 \
    glib2-devel \
    harfbuzz \
    harfbuzz-devel \
    fontconfig \
    fontconfig-devel \
    freetype \
    freetype-devel \
    libffi-devel
```

### 2. 安装 Python 依赖

```bash
pip install weasyprint==62.3
```

### 3. 配置环境变量（如果需要）

```bash
export LD_LIBRARY_PATH="/usr/lib64:$LD_LIBRARY_PATH"
echo 'export LD_LIBRARY_PATH="/usr/lib64:$LD_LIBRARY_PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Windows

### 方法 1：使用 GTK3 Runtime（推荐）

1. **下载并安装 GTK3 Runtime**

   访问 [GTK for Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)，下载最新版本的安装程序（例如 `gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe`）。

2. **运行安装程序**

   双击安装程序，按照提示完成安装。默认安装路径为 `C:\Program Files\GTK3-Runtime Win64`。

3. **添加到系统 PATH**

   - 右键点击"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑"
   - 添加以下路径：
     ```
     C:\Program Files\GTK3-Runtime Win64\bin
     ```
   - 点击"确定"保存

4. **安装 Python 依赖**

   ```cmd
   pip install weasyprint==62.3
   ```

5. **重启命令提示符或 PowerShell**

### 方法 2：使用 MSYS2（开发者推荐）

1. **安装 MSYS2**

   访问 [MSYS2 官网](https://www.msys2.org/)，下载并安装 MSYS2。

2. **安装依赖包**

   打开 MSYS2 终端，运行：

   ```bash
   pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-cairo mingw-w64-x86_64-glib2
   ```

3. **添加到系统 PATH**

   将 MSYS2 的 bin 目录添加到系统 PATH：
   ```
   C:\msys64\mingw64\bin
   ```

4. **安装 Python 依赖**

   ```cmd
   pip install weasyprint==62.3
   ```

---

## 验证安装

运行以下 Python 代码验证 WeasyPrint 是否正确安装：

```python
from weasyprint import HTML

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>测试中文字体</h1>
    <p>这是一个测试文档，用于验证 WeasyPrint 是否正确安装。</p>
    <p>Test English text and 中文文本。</p>
</body>
</html>
"""

try:
    pdf_bytes = HTML(string=html_content).write_pdf()
    with open('test.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print("✓ WeasyPrint 安装成功！已生成 test.pdf")
except Exception as e:
    print(f"✗ WeasyPrint 安装失败：{e}")
```

如果成功，会在当前目录生成 `test.pdf` 文件。

---

## 常见问题

### 1. macOS: `OSError: cannot load library 'libgobject-2.0-0'`

**原因**：环境变量未正确设置。

**解决方案**：
- 确保已添加环境变量到 `~/.zshrc`
- 重启终端或运行 `source ~/.zshrc`
- 如果使用 IDE，需要重启 IDE

### 2. Linux: `ImportError: cannot import name 'HTML' from 'weasyprint'`

**原因**：系统依赖未安装。

**解决方案**：
```bash
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

### 3. Windows: `OSError: no library called "cairo" was found`

**原因**：GTK3 Runtime 未安装或未添加到 PATH。

**解决方案**：
- 确保已安装 GTK3 Runtime
- 检查 `C:\Program Files\GTK3-Runtime Win64\bin` 是否在系统 PATH 中
- 重启命令提示符

### 4. 中文字体显示为方块

**原因**：系统缺少中文字体。

**解决方案**：

**macOS**：
```bash
# 系统自带中文字体，通常不需要额外安装
```

**Linux**：
```bash
sudo apt-get install fonts-noto-cjk fonts-wqy-zenhei
```

**Windows**：
- 确保系统已安装中文字体（如微软雅黑、宋体等）
- Windows 10/11 默认已包含中文字体

### 5. Conda 环境中的问题

如果在 Conda 环境中遇到库加载问题，尝试：

```bash
# 安装 conda-forge 版本
conda install -c conda-forge weasyprint
```

或者确保环境变量在激活 Conda 环境后仍然有效。

---

## 项目启动

配置完成后，启动后端服务：

```bash
cd /path/to/backend-fastapi
python -m uvicorn main:app --reload
```

如果一切正常，服务应该能够成功启动，并且 PDF 预览功能可以正常使用。

---

## 参考链接

- [WeasyPrint 官方文档](https://doc.courtbouillon.org/weasyprint/stable/)
- [WeasyPrint 安装指南](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)
- [WeasyPrint 故障排除](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#troubleshooting)

