<script lang="ts" setup>
import { computed, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElCheckbox,
  ElInput,
  ElOption,
  ElScrollbar,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
} from 'element-plus';

interface RouteItem {
  path: string;
  method: string;
  operation_id: string;
  summary: string;
  name?: string;
  code?: string;
  permission_type?: number;
  http_method?: number;
  is_active?: boolean;
  selected?: boolean;
}

interface Props {
  routes: RouteItem[];
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  'toggle-select': [route: RouteItem];
  'toggle-select-all': [];
  'update:routes': [routes: RouteItem[]];
}>();

// 路径分段选择 - 默认显示三个 select
const segmentValues = ref<(null | string)[]>(['api', null, null]);

// 获取路径的所有分段
function getPathSegments(routes: RouteItem[]): string[][] {
  const segments: string[][] = [];

  routes.forEach((route) => {
    const parts = route.path.split('/').filter(Boolean);
    parts.forEach((part, index) => {
      if (!segments[index]) {
        segments[index] = [];
      }
      if (!segments[index].includes(part)) {
        segments[index].push(part);
      }
    });
  });

  return segments.map((seg) => seg.sort());
}

// 获取当前段的可选值
function getSegmentOptions(segmentIndex: number): string[] {
  const allSegments = getPathSegments(props.routes);
  return allSegments[segmentIndex] || [];
}

// 过滤后的路由
const filteredRoutes = computed(() => {
  const selectedPath = segmentValues.value.filter((v) => v !== null).join('/');

  if (!selectedPath) return props.routes;

  return props.routes.filter((route) => {
    const routePath = route.path.replace(/^\//, '');
    return routePath.startsWith(selectedPath);
  });
});

// 已选择的路由数
const selectedCount = computed(() => {
  return props.routes.filter((r) => r.selected).length;
});

// 所有过滤后的路由是否都被选中
const allFilteredSelected = computed(() => {
  return (
    filteredRoutes.value.length > 0 &&
    filteredRoutes.value.every((r) => r.selected)
  );
});

// 检测重复的权限名称
const duplicateNames = computed(() => {
  const selectedRoutes = props.routes.filter((r) => r.selected);
  const nameCount = new Map<string, number>();
  const duplicates = new Set<string>();

  selectedRoutes.forEach((route) => {
    if (route.name) {
      const count = nameCount.get(route.name) || 0;
      nameCount.set(route.name, count + 1);
      if (count > 0) {
        duplicates.add(route.name);
      }
    }
  });

  return duplicates;
});

// 检测重复的权限编码
const duplicateCodes = computed(() => {
  const selectedRoutes = props.routes.filter((r) => r.selected);
  const codeCount = new Map<string, number>();
  const duplicates = new Set<string>();

  selectedRoutes.forEach((route) => {
    if (route.code) {
      const count = codeCount.get(route.code) || 0;
      codeCount.set(route.code, count + 1);
      if (count > 0) {
        duplicates.add(route.code);
      }
    }
  });

  return duplicates;
});

// 判断某个路由的名称是否重复
function isNameDuplicate(route: RouteItem): boolean {
  return route.name ? duplicateNames.value.has(route.name) : false;
}

// 判断某个路由的编码是否重复
function isCodeDuplicate(route: RouteItem): boolean {
  return route.code ? duplicateCodes.value.has(route.code) : false;
}

// 生成扩展的权限编码（添加路径后续段）
function generateExtendedCode(route: RouteItem): string {
  // 不使用 filter，保留空字符串以保持索引一致
  const parts = route.path.split('/');
  // parts[0] = '', parts[1] = 'api', parts[2] = 'core', parts[3] = 'user', parts[4+] = 额外段

  if (parts.length <= 4) {
    // 没有额外段，无法扩展
    return route.code || '';
  }

  // 获取原始编码的方法部分（例如 'user:read' 的 'user:read'）
  const baseCode = route.code || '';

  // 添加第4段（索引4）及之后的所有段
  const extraParts = parts.slice(4).filter(Boolean).join('_');

  return extraParts ? `${baseCode}_${extraParts}` : baseCode;
}

// 自动修复重复的权限编码
function fixDuplicateCodes() {
  const selectedRoutes = props.routes.filter((r) => r.selected);
  const codeMap = new Map<string, RouteItem[]>();

  // 按编码分组
  selectedRoutes.forEach((route) => {
    if (route.code) {
      if (!codeMap.has(route.code)) {
        codeMap.set(route.code, []);
      }
      codeMap.get(route.code)!.push(route);
    }
  });

  // 找出重复的编码并修复
  let fixedCount = 0;
  codeMap.forEach((routes) => {
    if (routes.length > 1) {
      // 有重复，需要修复
      routes.forEach((route) => {
        const extendedCode = generateExtendedCode(route);
        if (extendedCode !== route.code) {
          route.code = extendedCode;
          fixedCount++;
        }
      });
    }
  });

  if (fixedCount > 0) {
    emit('update:routes', [...props.routes]);
  }

  return fixedCount;
}

// 检查是否有重复（暴露给父组件）
function checkDuplicates(): { hasError: boolean; message: string } {
  const selectedRoutes = props.routes.filter((r) => r.selected);

  if (selectedRoutes.length === 0) {
    return { hasError: true, message: '请至少选择一个路由' };
  }

  // 检查是否还有重复（选中时已经自动修复过）
  const duplicateNameList = [...duplicateNames.value];
  const duplicateCodeList = [...duplicateCodes.value];

  if (duplicateNameList.length > 0 || duplicateCodeList.length > 0) {
    const messages: string[] = [];
    if (duplicateNameList.length > 0) {
      messages.push(`权限名称重复: ${duplicateNameList.join(', ')}`);
    }
    if (duplicateCodeList.length > 0) {
      messages.push(
        `权限编码重复: ${duplicateCodeList.join(', ')}（路径段不足，无法自动修复）`,
      );
    }
    return { hasError: true, message: messages.join('；') };
  }

  return { hasError: false, message: '' };
}

// 暴露方法给父组件
defineExpose({
  checkDuplicates,
});

// 获取方法 tag 类型
function getMethodTagType(
  method: string,
): 'danger' | 'info' | 'success' | 'warning' {
  const typeMap: Record<string, 'danger' | 'info' | 'success' | 'warning'> = {
    GET: 'info',
    POST: 'success',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'warning',
  };
  return typeMap[method] || 'info';
}

// 切换选择
function toggleSelect(route: RouteItem) {
  route.selected = !route.selected;

  // 如果是选中操作，立即检查并修复重复编码
  if (route.selected) {
    fixDuplicateCodes();
  }

  emit('update:routes', [...props.routes]);
}

// 全选/取消全选
function toggleSelectAll() {
  const shouldSelect = !allFilteredSelected.value;
  filteredRoutes.value.forEach((route) => {
    route.selected = shouldSelect;
  });

  // 如果是全选操作，立即检查并修复重复编码
  if (shouldSelect) {
    fixDuplicateCodes();
  }

  emit('update:routes', [...props.routes]);
}
</script>

<template>
  <div class="route-selector">
    <!-- 卡片容器 -->
    <ElCard class="routes-card" shadow="never">
      <!-- 卡片头部 -->
      <template #header>
        <div class="card-header">
          <!-- 左侧：搜索框 -->
          <div class="search-box">
            <div class="segment-selects">
              <div
                v-for="(_, index) in segmentValues"
                :key="index"
                class="segment-item"
              >
                <ElSelect
                  v-model="segmentValues[index]"
                  placeholder="选择路径段"
                  clearable
                  filterable
                  class="segment-select"
                >
                  <ElOption
                    v-for="option in getSegmentOptions(index)"
                    :key="option"
                    :label="option"
                    :value="option"
                  />
                </ElSelect>

                <!-- 最后一个 select 后添加加号按钮 -->
                <ElButton
                  v-if="index === segmentValues.length - 1"
                  type="primary"
                  link
                  size="small"
                  @click="segmentValues.push(null)"
                  class="add-segment-btn"
                >
                  +
                </ElButton>
              </div>
            </div>
          </div>

          <!-- 右侧：统计和全选 -->
          <div class="toolbar">
            <span class="stats">
              共 <strong>{{ filteredRoutes.length }}</strong> 个，已选
              <strong>{{ selectedCount }}</strong> 个
            </span>
            <ElButton type="primary" link size="small" @click="toggleSelectAll">
              {{ allFilteredSelected ? '取消全选' : '全选' }}
            </ElButton>
          </div>
        </div>
      </template>

      <!-- 卡片内容：路由列表 -->
      <ElScrollbar class="routes-list">
        <!-- 加载中 - 骨架屏 -->
        <div v-if="loading" class="routes-container">
          <ElSkeleton :loading="true" animated :throttle="0">
            <template #template>
              <div v-for="i in 8" :key="i" class="skeleton-item">
                <div class="skeleton-checkbox">
                  <ElSkeletonItem
                    variant="circle"
                    style="width: 16px; height: 16px"
                  />
                </div>
                <div class="skeleton-content">
                  <div class="skeleton-header">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 50px; height: 22px; border-radius: 4px"
                    />
                    <ElSkeletonItem
                      variant="text"
                      :style="{
                        width: `${150 + Math.random() * 100}px`,
                        height: '16px',
                      }"
                    />
                    <ElSkeletonItem
                      variant="text"
                      :style="{
                        width: `${80 + Math.random() * 60}px`,
                        height: '14px',
                      }"
                    />
                  </div>
                  <div class="skeleton-fields">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 32px; border-radius: 4px"
                    />
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 32px; border-radius: 4px"
                    />
                  </div>
                </div>
              </div>
            </template>
          </ElSkeleton>
        </div>

        <div v-else-if="filteredRoutes.length === 0" class="empty-state">
          <p>暂无路由数据</p>
        </div>

        <div v-else class="routes-container">
          <div
            v-for="route in filteredRoutes"
            :key="`${route.path}-${route.method}`"
            class="route-item"
            :class="{ selected: route.selected }"
          >
            <!-- 复选框 -->
            <div class="route-checkbox">
              <ElCheckbox
                :model-value="route.selected"
                @change="toggleSelect(route)"
              />
            </div>

            <!-- 路由信息 -->
            <div class="route-info">
              <!-- 方法和路径 -->
              <div class="route-header">
                <ElTag
                  :type="getMethodTagType(route.method)"
                  class="method-tag"
                >
                  {{ route.method }}
                </ElTag>

                <span class="route-path">{{ route.path }}</span>
                <!-- 描述 -->
                <span v-if="route.summary" class="route-summary">
                  {{ route.summary }}
                </span>
              </div>

              <!-- 编辑字段 -->
              <div class="route-fields">
                <div class="field-group">
                  <label>权限名称</label>
                  <ElInput
                    v-model="route.name"
                    placeholder="权限名称"
                    size="small"
                    :class="{
                      'is-error': route.selected && isNameDuplicate(route),
                    }"
                  />
                  <span
                    v-if="route.selected && isNameDuplicate(route)"
                    class="error-text"
                  >
                    权限名称重复
                  </span>
                </div>
                <div class="field-group">
                  <label>权限编码</label>
                  <ElInput
                    v-model="route.code"
                    placeholder="权限编码"
                    size="small"
                    :class="{
                      'is-error': route.selected && isCodeDuplicate(route),
                    }"
                  />
                  <span
                    v-if="route.selected && isCodeDuplicate(route)"
                    class="error-text"
                  >
                    权限编码重复
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ElScrollbar>
    </ElCard>
  </div>
</template>

<style scoped lang="scss">
.route-selector {
  display: flex;
  flex-direction: column;
  height: 100%;

  .routes-card {
    display: flex;
    flex-direction: column;
    height: 100%;

    :deep(.el-card__header) {
      flex-shrink: 0;
      padding: 12px 16px;
      border-bottom: 1px solid hsl(var(--border));
    }

    :deep(.el-card__body) {
      display: flex;
      flex: 1;
      flex-direction: column;
      padding: 0;
      overflow: hidden;
    }

    .card-header {
      display: flex;
      gap: 16px;
      align-items: center;
      justify-content: space-between;

      .search-box {
        flex: 1;

        .segment-selects {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          align-items: center;

          .segment-item {
            display: flex;
            gap: 4px;
            align-items: center;

            .segment-select {
              flex-shrink: 0;
              width: 120px;

              :deep(.el-input__wrapper) {
                border-radius: 6px;
                box-shadow: 0 1px 2px hsl(var(--foreground) / 5%);
              }
            }

            .add-segment-btn {
              padding: 0 8px;
              font-size: 16px;
              line-height: 1;
            }
          }
        }
      }

      .toolbar {
        display: flex;
        flex-shrink: 0;
        gap: 12px;
        align-items: center;
        font-size: 13px;
        white-space: nowrap;

        .stats {
          color: hsl(var(--foreground) / 65%);

          strong {
            font-weight: 600;
            color: hsl(var(--primary));
          }
        }
      }
    }
  }

  .routes-list {
    flex: 1;
    min-height: 0;
    background-color: hsl(var(--background));

    :deep(.el-scrollbar__wrap) {
      padding: 0;
    }

    :deep(.el-scrollbar__view) {
      display: flex;
      flex-direction: column;
    }

    .skeleton-item {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 12px;
      align-items: start;
      padding: 12px;
      background-color: hsl(var(--background) / 50%);
      border: 1px solid hsl(var(--border));
      border-radius: 6px;

      .skeleton-checkbox {
        padding-top: 2px;
      }

      .skeleton-content {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        min-width: 0;

        .skeleton-header {
          display: flex;
          grid-column: 1 / -1;
          gap: 8px;
          align-items: center;
        }

        .skeleton-fields {
          display: grid;
          grid-template-columns: 1fr 1fr;
          grid-column: 1 / -1;
          gap: 8px;
        }
      }
    }

    .empty-state {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;

      p {
        font-size: 14px;
        color: hsl(var(--foreground) / 65%);
      }
    }

    .routes-container {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 8px;
    }
  }

  .route-item {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 12px;
    align-items: start;
    padding: 12px;
    background-color: hsl(var(--background) / 50%);
    border: 1px solid hsl(var(--border));
    border-radius: 6px;
    transition: all 0.2s ease;

    &:hover {
      background-color: hsl(var(--background) / 80%);
      border-color: hsl(var(--border) / 80%);
    }

    &.selected {
      background-color: hsl(var(--primary) / 5%);
      border-color: hsl(var(--primary));
      box-shadow: 0 0 0 2px hsl(var(--primary) / 10%);
    }

    .route-checkbox {
      display: flex;
      flex-shrink: 0;
      align-items: flex-start;
      padding-top: 2px;
      cursor: pointer;

      :deep(.el-checkbox) {
        margin-right: 0;
      }
    }

    .route-info {
      display: grid;
      flex: 1;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      min-width: 0;

      .route-header {
        display: flex;
        grid-column: 1 / -1;
        gap: 8px;
        align-items: center;

        .method-tag {
          flex-shrink: 0;
        }

        .route-path {
          font-family: Monaco, Menlo, 'Ubuntu Mono', monospace;
          font-size: 13px;
          color: hsl(var(--foreground));
          word-break: break-all;
        }

        .route-summary {
          font-size: 12px;
          line-height: 1.4;
          color: hsl(var(--foreground) / 65%);
        }
      }

      .route-fields {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-column: 1 / -1;
        gap: 8px;

        .field-group {
          display: flex;
          flex-direction: column;
          gap: 4px;

          label {
            font-size: 11px;
            font-weight: 500;
            color: hsl(var(--foreground) / 65%);
          }

          .error-text {
            margin-top: 2px;
            font-size: 11px;
            color: var(--el-color-danger);
          }

          :deep(.el-input__wrapper) {
            border-radius: 4px;
          }

          :deep(.is-error .el-input__wrapper) {
            border-color: var(--el-color-danger);
            box-shadow: 0 0 0 1px var(--el-color-danger-light-7);
          }

          :deep(.is-error .el-input__wrapper:hover) {
            border-color: var(--el-color-danger);
          }

          :deep(.is-error .el-input__wrapper.is-focus) {
            border-color: var(--el-color-danger);
            box-shadow: 0 0 0 1px var(--el-color-danger-light-7);
          }
        }
      }
    }
  }
}
</style>
