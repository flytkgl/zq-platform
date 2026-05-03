# 登录日志管理

## 功能概述

登录日志管理模块用于记录和查看用户的登录操作，包括成功和失败的登录尝试，帮助管理员监控系统安全。

## 目录结构

```
login-log/
├── index.vue              # 登录日志主页面
├── data.ts                # 数据配置（列定义、搜索表单等）
├── modules/
│   └── detail-drawer.vue  # 登录日志详情抽屉
└── README.md             # 功能说明文档
```

## 主要功能

### 1. 登录日志列表
- ✅ 分页查询登录日志
- ✅ 多条件筛选（用户名、IP、状态、失败原因、浏览器、操作系统、设备类型、时间范围）
- ✅ 显示登录状态（成功/失败）
- ✅ 显示登录IP和属地
- ✅ 显示浏览器、操作系统、设备类型
- ✅ 支持多选和批量操作

### 2. 登录日志详情
- ✅ 查看完整的登录信息
- ✅ 失败原因详情
- ✅ 用户代理信息
- ✅ 登录时长
- ✅ 会话ID

### 3. 日志管理
- ✅ 删除单条日志
- ✅ 批量删除日志
- ✅ 刷新列表

## 数据字段说明

### 登录状态 (status)
- `0` - 失败
- `1` - 成功

### 失败原因 (failure_reason)
- `0` - 未知错误
- `1` - 用户不存在
- `2` - 密码错误
- `3` - 用户已禁用
- `4` - 用户已锁定
- `5` - 用户不激活
- `6` - 账户异常
- `7` - 其他错误

### 设备类型 (device_type)
- `desktop` - 桌面设备
- `mobile` - 移动设备
- `tablet` - 平板设备
- `other` - 其他设备

## API 接口

### 基础接口

```typescript
// 获取登录日志列表
getLoginLogListApi(params?: LoginLogListParams): Promise<PaginatedResponse<LoginLog>>

// 获取登录日志详情
getLoginLogDetailApi(logId: string): Promise<LoginLog>

// 删除登录日志
deleteLoginLogApi(logId: string): Promise<void>

// 批量删除登录日志
batchDeleteLoginLogApi(ids: string[]): Promise<void>
```

### 统计接口

```typescript
// 获取登录统计概览
getLoginStatsApi(days?: number): Promise<LoginLogStats>

// 获取IP登录统计
getIpStatsApi(days?: number, limit?: number): Promise<LoginLogIpStats[]>

// 获取设备登录统计
getDeviceStatsApi(days?: number): Promise<LoginLogDeviceStats[]>

// 获取用户登录统计
getUserStatsApi(days?: number, limit?: number): Promise<LoginLogUserStats[]>

// 获取每日登录统计
getDailyStatsApi(days?: number): Promise<LoginLogDailyStats[]>
```

### 用户相关接口

```typescript
// 获取用户的登录日志
getUserLoginLogsApi(userId: string, days?: number, page?: number, pageSize?: number): Promise<PaginatedResponse<LoginLog>>

// 获取用户登录次数
getUserLoginCountApi(userId: string, days?: number): Promise<{...}>

// 获取用户最后一次登录
getUserLastLoginApi(userId: string): Promise<LoginLog>

// 获取用户登录过的IP地址
getUserLoginIpsApi(userId: string, days?: number): Promise<{...}>
```

### 安全相关接口

```typescript
// 获取可疑登录记录
getSuspiciousLoginsApi(failedThreshold?: number, hours?: number): Promise<{...}>

// 获取用户登录失败次数
getFailedAttemptsApi(username: string, hours?: number): Promise<{...}>
```

### 维护接口

```typescript
// 清理旧的登录日志
cleanOldLogsApi(days?: number): Promise<{deleted_count: number}>
```

## 使用说明

### 导入 API
由于类型冲突问题，请直接从 login-log 模块导入：

```typescript
import {
  getLoginLogListApi,
  getLoginLogDetailApi,
  deleteLoginLogApi,
  batchDeleteLoginLogApi,
} from '#/api/core/login-log';
```

### 访问页面
页面路由需要在路由配置中添加，路径为：`/core/login-log`

### 权限要求
- 查看日志：需要 `login-log:read` 权限
- 删除日志：需要 `login-log:delete` 权限

## 表格列配置

| 字段 | 标题 | 宽度 | 说明 |
|------|------|------|------|
| username | 用户名 | 120px | 固定在左侧 |
| status | 登录状态 | 100px | 标签显示（成功/失败） |
| login_ip | 登录IP | 140px | - |
| ip_location | IP属地 | 150px | - |
| failure_reason | 失败原因 | 120px | 默认隐藏 |
| failure_message | 失败信息 | 180px | 默认隐藏 |
| browser_type | 浏览器 | 120px | - |
| os_type | 操作系统 | 120px | - |
| device_type | 设备类型 | 100px | 标签显示 |
| duration | 登录时长 | 120px | 默认隐藏 |
| remark | 备注 | 150px | 默认隐藏 |
| sys_create_datetime | 登录时间 | 180px | 可排序 |
| operation | 操作 | 150px | 详情、删除 |

## 搜索表单配置

- 用户名（Input）
- 登录IP（Input）
- 登录状态（Select）
- 失败原因（Select）
- 浏览器（Input）
- 操作系统（Input）
- 设备类型（Select）
- 开始时间（DatePicker - datetime）
- 结束时间（DatePicker - datetime）

## 安全考虑

1. **数据保护**：登录日志包含敏感信息（IP地址、用户代理等），应限制访问权限
2. **日志保留**：建议定期清理旧日志，避免数据库膨胀
3. **异常监控**：关注失败登录记录，及时发现安全问题
4. **可疑行为**：使用可疑登录接口监控短时间内多次失败的登录尝试

## 扩展功能（未来）

- [ ] 导出日志为 Excel/CSV
- [ ] 登录统计图表展示
- [ ] 可疑IP自动封禁
- [ ] 登录地图可视化
- [ ] 实时登录监控
- [ ] 邮件/短信告警

## 注意事项

1. **类型导入**：由于 `PaginatedResponse` 类型在多个模块中重复定义，导入 login-log API 时请直接从模块导入，不要从 `#/api/core` 导入
2. **时间格式**：搜索时间使用 `YYYY-MM-DD HH:mm:ss` 格式
3. **批量操作**：批量删除前会显示涉及的用户名列表
4. **详情展示**：根据登录状态（成功/失败）动态显示相关字段

## 技术栈

- **Vue 3** - 框架
- **TypeScript** - 类型支持
- **Element Plus** - UI 组件库
- **VXE Table** - 表格组件
- **Vben** - 企业级前端框架

## 维护者

如有问题或建议，请联系开发团队。
