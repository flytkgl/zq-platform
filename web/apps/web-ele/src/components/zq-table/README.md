# ZqTable 组件使用文档

`ZqTable` 是基于 `element-plus` 的 `Table V2` (虚拟滚动表格) 封装的高级表格组件，旨在提供与 `vben-admin` 中 `vxe-table` 封装 (`useVbenVxeGrid`) 一致的开发体验，同时解决大数据量渲染性能问题。

## 特性

*   🚀 **高性能**：基于虚拟滚动，轻松支撑万级数据渲染。
*   🛠 **高度集成**：内置搜索表单 (`vben-form`)、工具栏、分页器。
*   ✨ **API 统一**：与 `useVbenVxeGrid` API 保持一致，降低迁移成本。
*   📏 **高度自适应**：自动计算表格高度，适应容器大小。
*   🎨 **Element Plus 风格**：完全契合 Element Plus 设计规范。

## 基础用法

使用 `useZqTable` hook 创建表格实例，并传递配置项。

```vue
<script setup lang="ts">
import { useZqTable } from '@/components/zq-table';

// 定义列（遵循 Element Plus V2 Column 格式）
const columns = [
  { key: 'name', dataKey: 'name', title: '姓名', width: 150 },
  { key: 'age', dataKey: 'age', title: '年龄', width: 100 },
  { key: 'address', dataKey: 'address', title: '地址', width: 300 },
];

// 模拟数据接口
const fetchList = async ({ page, form }) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        items: Array.from({ length: page.pageSize }).map((_, i) => ({
          id: i,
          name: `User ${i + (page.currentPage - 1) * page.pageSize}`,
          age: 18 + i,
          address: 'Shanghai',
        })),
        total: 100,
      });
    }, 500);
  });
};

const [Table] = useZqTable({
  tableTitle: '示例表格',
  gridOptions: {
    columns,
    proxyConfig: {
      ajax: {
        query: fetchList,
      },
    },
  },
});
</script>

<template>
  <!-- 重要：父容器必须有高度，否则表格高度为 0 -->
  <div class="h-[500px]">
     <Table />
  </div>
</template>
```

## API 说明

### `useZqTable(options)`

接收一个配置对象 `ZqTableProps`，返回 `[TableComponent, TableApi]`。

#### 配置项 (`ZqTableProps`)

| 属性 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `gridOptions.columns` | `Column[]` | 列配置，详见 Element Plus Table V2 文档 | `[]` |
| `gridOptions.data` | `any[]` | 静态数据（不使用 proxyConfig 时） | `[]` |
| `gridOptions.proxyConfig` | `ZqProxyConfig` | 数据代理配置，用于自动加载数据 | - |
| `gridOptions.pagerConfig` | `ZqPagerConfig` | 分页配置 | `{ enabled: true, pageSize: 20 }` |
| `gridOptions.toolbarConfig` | `ZqToolbarConfig` | 工具栏配置 | `{ search: false, refresh: true, zoom: true, custom: true }` |
| `formOptions` | `VbenFormProps` | 搜索表单配置 | - |
| `showSearchForm` | `boolean` | 是否显示搜索表单 | `true` |
| `tableTitle` | `string` | 表格标题 | - |

#### `proxyConfig`

```typescript
interface ZqProxyConfig {
  autoLoad?: boolean; // 是否自动加载数据，默认为 true
  ajax?: {
    // 核心查询方法
    // params 包含:
    //   page: { currentPage, pageSize, total }
    //   form: 表单数据
    //   sort: 排序数据
    query?: (params: { page: any; form: any; sort: any }) => Promise<any>;
  };
}
```

#### `TableApi`

`useZqTable` 返回的第二个参数，用于操作表格。

| 方法 | 说明 |
| :--- | :--- |
| `reload(params?: any)` | 重新加载数据，可传入额外的查询参数（合并到 form 中） |
| `query(params?: any)` | 别名 reload |
| `setLoading(loading: boolean)` | 手动设置加载状态 |
| `toggleSearchForm(show?: boolean)` | 切换搜索表单显示状态 |
| `getFormApi()` | 获取内部 Form 实例的 API |

## 插槽 (Slots)

| 插槽名 | 说明 |
| :--- | :--- |
| `table-title` | 自定义标题区域 |
| `toolbar-actions` | 工具栏左侧操作区（标题右侧） |
| `toolbar-tools` | 工具栏右侧工具区（刷新按钮左侧） |
| `form-[field]` | 自定义表单字段插槽 |
| `empty` | 自定义空状态 |

## 注意事项

1.  **高度问题**：`zq-table` 内部使用 `useResizeObserver` 监听父容器大小来设置表格高度。因此**必须确保父容器有明确的高度**（如 `h-full` 且外层有高度，或者固定 `h-[500px]`），否则表格高度可能为 0，导致无法显示数据。
2.  **列宽**：Table V2 的列宽必须是数字，建议在 `columns` 配置中显式指定 `width`。
3.  **样式**：默认占满父容器 (`h-full`)。
