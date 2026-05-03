# ZQ Platform

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](backend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-green.svg)](backend/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)](web/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](web/)

**A Full-Stack Enterprise Low-Code / No-Code Development Platform Based on FastAPI + Vue 3**

English | [简体中文](README.md)

</div>

## 🌐 Links

- **Official Website**: <https://zq-platform.com/>
- **Demo Link**: <https://opensource.zq-platform.com/>
- **Demo Account**: `zhangwei`
- **Demo Password**: `admin123`

***

## 📖 Introduction

ZQ Platform is a full-featured enterprise-level development platform with a decoupled frontend-backend architecture. The backend is built on **FastAPI** asynchronous framework, and the frontend is powered by **Vue 3** + **Element Plus** + **Vben Admin 5.x**.

The platform integrates RBAC permission management, organization management, **online form/page design (no-code)**, instant messaging, AI chat, third-party login and organization sync, system monitoring, scheduled tasks, data source management, code generator, and many other enterprise-grade modules, significantly accelerating enterprise application development.

## 🎯 No-Code Capabilities — Fully Open-Source, Free, and Unrestricted

The no-code (online development) module of ZQ Platform is one of its core highlights. Compared to mainstream no-code/low-code platforms on the market, it offers the significant advantages of being **fully open-source, completely free, and entirely unrestricted**.

### Comparison with Similar Platforms

| Dimension              | ZQ Platform                                                     | DingTalk YiDa                                | Baidu AiSuDa                                           | NocoBase                                              |
| ---------------------- | --------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------- |
| **License**            | fully open-source                                               | ❌ Closed-source commercial                   | ❌ Closed-source commercial                             | ⚠️ AGPL 3.0 (copyleft, commercial restrictions)       |
| **Free to Use**        | ✅ Completely free, no hidden costs                              | ❌ Pay per user/form/process                  | ❌ Pay per edition, feature limitations                 | ⚠️ Community edition limited, enterprise edition paid |
| **User Limit**         | ✅ Unlimited                                                     | ❌ Limited by plan                            | ❌ Limited by edition                                   | ⚠️ Community edition has user limits                  |
| **Deployment**         | ✅ Self-hosted, data fully under your control                    | ⚠️ SaaS-focused, very high self-hosting cost | ⚠️ SaaS-focused, self-hosting needs enterprise edition | ✅ Supports self-hosting                               |
| **Custom Development** | ✅ Unlimited, can modify source code freely                      | ❌ Not supported                              | ❌ Limited support                                      | ⚠️ AGPL restricts commercial customization            |
| **Commercial Use**     | ✅ Apache 2.0 allows free + LICENSE\_SUPPLEMENTAL commercial use | ❌ Must purchase commercial license           | ❌ Must purchase commercial license                     | ⚠️ AGPL requires purchased license for commercial use |
| **Database Support**   | PostgreSQL / MySQL                                              | Cloud database only                          | Cloud database only                                    | PostgreSQL                                            |
| **Frontend Tech**      | Vue 3 + Element Plus (mainstream)                               | Closed stack, cannot customize               | Closed stack                                           | React + Ant Design                                    |
| **Backend Tech**       | Python FastAPI (async, high-performance)                        | Closed                                       | Closed                                                 | Node.js + Koa                                         |

### No-Core Features

#### 📝 Online Form Designer

- **Drag-and-Drop Design**: Intuitive drag-and-drop operations to build complex forms without writing any code
- **Rich Component Library**: 30+ components including text input, number, date, dropdown select, cascade select, file upload, rich text, sub-forms, etc.
- **Complex Layout**: Supports multi-column, grouping, table layout, tabs, and other complex page layouts
- **Conditional Logic**: Field visibility conditions, validation rules, and linkage logic configuration
- **Mobile Adaptation**: Automatically adapts to both PC and mobile displays

#### 📄 Online Page Designer

- **Visual Page Composition**: Freely combine forms, charts, data tables and other components into complete business pages
- **Data Binding**: Supports data source binding and API integration for real-time interaction with backend data
- **Permission Integration**: Page-level access control, seamlessly integrated with the RBAC permission system

#### 📊 Dashboard Designer

- **Rich Chart Components**: 20+ chart types including line, bar, pie, radar, funnel, heatmap, sankey, K-line, etc.
- **Business Components**: Announcement list, to-do items, quick links, ranking list, server monitor, weather widget, etc.
- **Data Filtering**: Supports interactive data filtering with date picker, input search, etc.
- **Free Layout**: Drag-and-drop free layout with customizable size and position

#### 🔗 Data Management

- **Data Source Management**: Connect external databases (PostgreSQL / MySQL / SQL Server) as data sources
- **Form Data Management**: Auto-generates list, detail, edit, and delete functionality for form data
- **Data Import/Export**: Supports Excel format data import and export

### Use Cases

- **Enterprise Internal Systems**: OA, CRM, ERP, inventory management, project management, etc.
- **Business Process Digitalization**: Approval workflows, ticketing systems, reporting systems, etc.
- **Rapid Prototyping**: Quick validation and iteration of business requirements
- **SaaS Platform Construction**: Multi-tenant application development
- **Data Collection & Analysis**: Surveys, data gathering, statistical analysis

***

## 🏗 Tech Stack

### Backend

| Technology                                                         | Description             |
| ------------------------------------------------------------------ | ----------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)                           | Web framework (0.121+)  |
| [SQLAlchemy 2.0](https://www.sqlalchemy.org/)                      | Async ORM               |
| [Alembic](https://alembic.sqlalchemy.org/)                         | Database migrations     |
| [PostgreSQL 16+](https://www.postgresql.org/) / MySQL / SQL Server | Database                |
| [Redis](https://redis.io/)                                         | Cache & messaging       |
| [APScheduler 4.x](https://apscheduler.readthedocs.io/)             | Task scheduling         |
| [MinIO](https://min.io/) / OSS / Azure Blob                        | File storage            |
| [Qdrant](https://qdrant.tech/)                                     | Vector database (RAG)   |
| [OpenAI](https://openai.com/) / Anthropic / DashScope              | AI LLM integration      |
| [WebSocket](https://websockets.readthedocs.io/)                    | Real-time communication |

### Frontend

| Technology                                                 | Description                              |
| ---------------------------------------------------------- | ---------------------------------------- |
| [Vue 3](https://vuejs.org/)                                | Frontend framework                       |
| [TypeScript](https://www.typescriptlang.org/)              | Type safety                              |
| [Element Plus](https://element-plus.org/)                  | UI component library                     |
| [Vben Admin 5.x](https://github.com/vbenjs/vue-vben-admin) | Admin framework                          |
| [Vite](https://vitejs.dev/)                                | Build tool                               |
| [Pinia](https://pinia.vuejs.org/)                          | State management                         |
| [Vue Router](https://router.vuejs.org/)                    | Routing                                  |
| [i18n](https://vue-i18n.intlify.nuxt.dev/)                 | Internationalization (zh-CN/en-US/zh-TW) |
| [ECharts](https://echarts.apache.org/)                     | Chart visualization                      |
| [Tiptap](https://tiptap.dev/)                              | Rich text editor                         |
| [CodeMirror](https://codemirror.net/)                      | Code editor                              |

## ✨ Key Features

### 🔐 User & Permissions

- **User Management**: Full CRUD, avatar upload, password policies
- **Role Management**: RBAC-based role permission assignment
- **Menu Management**: Dynamic menu configuration with permission control
- **Department Management**: Tree-based organization structure
- **Position Management**: Position association and staffing
- **Resource Permissions**: Granular field-level permission control
- **Data Permissions**: Department/user-based data scope isolation

### 🏢 Organization

- **Org Chart**: Visual organization chart
- **Department Tree**: Unlimited hierarchical department management
- **Enterprise Sync**: DingTalk, Feishu (Lark), WeCom organization/user sync

### 🔗 Third-Party Integration

- **OAuth Login**: Gitee, GitHub, QQ, Google, WeChat, Microsoft, DingTalk, Feishu, WeCom
- **Notifications**: Email (SMTP), SMS (Aliyun/Tencent), DingTalk bot, Feishu bot, WeCom bot, WeChat Official Account
- **File Storage**: Local storage, MinIO, Aliyun OSS, Azure Blob Storage

### 📱 No-Code Capabilities

- **Online Form Designer**: Drag-and-drop form builder with complex form design
- **Form Data Management**: Form data CRUD with dynamic queries
- **Online Page Designer**: Visual page editor
- **Dashboard Designer**: Drag-and-drop dashboard builder with rich chart components
- **Code Generator**: Multiple encoding modes (date sequence, serial numbers, etc.)

### 💬 Instant Messaging

- **Real-time Chat**: WebSocket-based private and group chat
- **Message Management**: Unread counts, mute notifications, pinned conversations
- **System Notifications**: System alerts and announcement management

### 🤖 AI Capabilities

- **AI Chat**: Integration with OpenAI, Anthropic (Claude), DashScope (Tongyi Qianwen) and more
- **Knowledge Base**: RAG (Retrieval-Augmented Generation) based on Qdrant vector database

### ⚙️ System Tools

- **Data Dictionary**: Business dictionary management (tree/list)
- **System Configuration**: Dynamic system parameter configuration
- **UI Configuration**: Frontend preference settings (dynamically loaded from backend)
- **Scheduled Tasks**: APScheduler-based task scheduling management
- **File Management**: File upload, preview, chunked upload
- **Data Source Manager**: External database connection management
- **API Tokens**: API access token management
- **Region Manager**: Geographic data management

### 🌐 Internationalization

- Chinese Simplified, Chinese Traditional, English
- Fully internationalized frontend UI
- Backend error message i18n support

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20.10+
- pnpm 9.12+
- PostgreSQL 16+
- Redis

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env/example.env env/dev.env
# Edit env/dev.env to configure database connection, etc.

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd web

# Install dependencies
pnpm install

# Start development server (Element Plus version by default)
pnpm dev

```

Visit <http://localhost:5777> to access the system.

## 🏛 Project Structure

```
zq-platform/
├── backend/                          # Backend Python service
│   ├── app/                          # Core application modules
│   │   ├── base_model.py            # Base model
│   │   ├── base_schema.py           # Common schemas
│   │   ├── base_service.py          # Base service
│   │   ├── config.py                # System configuration
│   │   ├── database.py              # Database connection
│   │   └── ...
│   ├── core/                         # Core business modules
│   │   ├── auth/                    # Authentication
│   │   ├── user/                    # User management
│   │   ├── role/                    # Role management
│   │   ├── menu/                    # Menu management
│   │   ├── dept/                    # Department management
│   │   ├── permission/              # Permission management
│   │   ├── chat/                    # Instant messaging
│   │   ├── file_manager/            # File management
│   │   ├── message/                 # Notifications
│   │   ├── oauth/                   # Third-party login
│   │   ├── code_generator/          # Code generator
│   │   ├── data_source/             # Data source management
│   │   ├── system_config/           # System configuration
│   │   ├── ui_config/               # UI configuration
│   │   ├── server_monitor/          # Server monitoring
│   │   ├── redis_monitor/           # Redis monitoring
│   │   ├── database_monitor/        # Database monitoring
│   │   ├── redis_manager/           # Redis manager
│   │   ├── database_manager/        # Database manager
│   │   ├── dingtalk_sync/           # DingTalk sync
│   │   ├── feishu_sync/             # Feishu sync
│   │   ├── wecom_sync/              # WeCom sync
│   │   ├── application/             # Application management
│   │   ├── device/                  # Device management
│   │   ├── region/                  # Region management
│   │   ├── login_log/               # Login logs
│   │   ├── api_token/               # API tokens
│   │   ├── link_preview/            # Link preview
│   │   ├── dict/                    # Data dictionary
│   │   ├── post/                    # Position management
│   │   └── resource_scope/          # Resource permissions
│   ├── online_dev/                   # Online development
│   │   ├── form_manager/            # Form management
│   │   ├── form_data_manager/       # Form data management
│   │   └── page_manager/            # Page management
│   ├── scheduler/                    # Scheduled tasks
│   ├── zq_demo/                      # Demo module
│   ├── alembic/                      # Database migrations
│   ├── main.py                       # Application entrypoint
│   └── requirements.txt              # Python dependencies
│
├── web/                              # Frontend project
│   ├── apps/
│   │   └── web-ele/                 # Element Plus app version
│   │       └── src/
│   │           ├── api/             # API interfaces
│   │           ├── components/      # Business components
│   │           ├── views/           # Page views
│   │           ├── router/          # Route configuration
│   │           ├── store/           # State management
│   │           ├── locales/         # i18n
│   │           └── layouts/         # Layout components
│   ├── packages/                     # Shared packages
│   │   ├── @core/                   # Core packages (UI components, utils, etc.)
│   │   ├── effects/                 # Business logic
│   │   ├── constants/               # Constants
│   │   ├── hooks/                   # Composables
│   │   ├── icons/                   # Icon library
│   │   ├── locales/                 # Internationalization
│   │   ├── preferences/             # User preferences
│   │   ├── request/                 # HTTP requests
│   │   ├── stores/                  # State management
│   │   ├── styles/                  # Styles
│   │   ├── types/                   # TypeScript types
│   │   └── utils/                   # Utility functions
│   └── package.json                  # Frontend dependencies
│
└── README.md                         # Project documentation
```

## 📸 Screenshots

> (Add project screenshots here)

## ✅ Environment Requirements

| Dependency | Version  |
| ---------- | -------- |
| Python     | >= 3.12  |
| Node.js    | >= 20.10 |
| pnpm       | >= 9.12  |
| PostgreSQL | >= 16    |
| Redis      | >= 6.0   |

## 🤝 Contributing

Issues and Pull Requests are welcome to help improve the project.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project adopts a dual-license structure:

- **Core License**: [Apache License 2.0](LICENSE) — Standard Apache 2.0 open-source license, permitting free use, modification, and redistribution
- **Supplemental Terms**: [ZQ-Platform Public License Supplemental Terms](LICENSE_SUPPLEMENTAL) — Additional terms governing attribution ("powered by ZQ-Platform") and trademark usage

By using this software, you agree to comply with all terms in both documents.

## 📞 Contact

- **Official Website**: <https://zq-platform.com/>
- **Source Code**: <https://github.com/jiangzhikj/zq-platform>
- **Full Version Demo**: <https://demo.zq-platform.com/>
- **Open-Source Demo**: <https://opensource.zq-platform.com/>
- **Author Email**: <jiangzhikj@outlook.com>
- **Issues**: [GitHub Issues](https://github.com/jiangzhikj/zq-platform/issues)

