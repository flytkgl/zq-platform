<script lang="ts" setup>
import type { Dict } from '#/api/core/dict';

import { computed, onMounted, ref } from 'vue';

import { IconifyIcon, Plus, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
  ElTooltip,
} from 'element-plus';

import { deleteDictApi, getDictListApi } from '#/api/core/dict';
import { useAppContextStore } from '#/store/app-context';

import DictFormModal from './dict-form-modal.vue';

const emit = defineEmits<{
  select: [dictId: string | undefined];
}>();

const appContextStore = useAppContextStore();

const dictList = ref<Dict[]>([]);
const loading = ref(false);
const selectedDictId = ref<string>();
const searchKeyword = ref<string>('');
const hoveredDictId = ref<string>();
const dictFormModalRef = ref<InstanceType<typeof DictFormModal>>();

// 计算过滤后的字典列表
const filteredDictList = computed(() => {
  if (!searchKeyword.value.trim()) {
    return dictList.value;
  }

  const keyword = searchKeyword.value.toLowerCase();
  return dictList.value.filter(
    (dict) =>
      dict.name.toLowerCase().includes(keyword) ||
      dict.code.toLowerCase().includes(keyword),
  );
});

async function fetchDictList() {
  try {
    loading.value = true;
    const response = await getDictListApi({
      page: 1,
      pageSize: 100,
      applicationId: appContextStore.currentApp?.id,
    });
    dictList.value = response.items || [];

    // 自动选中第一个字典
    if (dictList.value.length > 0 && !selectedDictId.value) {
      const firstDict = dictList.value.at(0);
      if (firstDict) {
        selectedDictId.value = firstDict.id;
        emit('select', firstDict.id);
      }
    }
  } finally {
    loading.value = false;
  }
}

/**
 * 处理字典选择
 */
function onDictSelect(dictId: string) {
  selectedDictId.value = dictId;
  emit('select', dictId);
}

/**
 * 打开添加字典对话框
 */
function onAddDict() {
  dictFormModalRef.value?.open();
}

/**
 * 打开编辑字典对话框
 */
function onEditDict(dict: Dict, e?: Event) {
  e?.stopPropagation();
  dictFormModalRef.value?.open(dict);
}

/**
 * 删除字典
 */
async function onDeleteDict(dict: Dict, e?: Event) {
  e?.stopPropagation();

  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [dict.name]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deleteDictApi(dict.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [dict.name]));

        // 如果删除的是当前选中的字典，清除选中状态
        if (selectedDictId.value === dict.id) {
          selectedDictId.value = undefined;
          emit('select', undefined);
        }

        await fetchDictList();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 添加字典成功后的回调
 */
async function onDictFormSuccess() {
  ElMessage.success($t('ui.actionMessage.createSuccess', [$t('dict.name')]));
  await fetchDictList();
}

onMounted(() => {
  fetchDictList();
});
</script>

<template>
  <ElCard shadow="never" style="border: none" class="flex h-full flex-col">
    <DictFormModal ref="dictFormModalRef" @success="onDictFormSuccess" />

    <!-- 搜索和添加区域 -->
    <div class="mb-4 flex gap-2">
      <ElInput
        v-model="searchKeyword"
        :placeholder="$t('common.search')"
        clearable
        :prefix-icon="Search"
      />
      <ElButton :icon="Plus" @click="onAddDict" />
    </div>

    <!-- 字典列表 -->
    <div class="flex-1 overflow-auto">
      <ElSkeleton :loading="loading" animated :count="8">
        <template #template>
          <div class="space-y-1">
            <div v-for="i in 8" :key="i" class="dict-skeleton-item">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 40px"
              />
            </div>
          </div>
        </template>
        <template #default>
          <div class="space-y-2">
            <div
              v-for="dict in filteredDictList"
              :key="dict.id"
              class="dict-item cursor-pointer rounded-[8px] px-3 py-2 transition-colors"
              :class="[
                selectedDictId === dict.id
                  ? 'bg-primary/15 dark:bg-accent text-primary'
                  : 'hover:bg-[var(--el-fill-color-light)]',
              ]"
              @mouseenter="hoveredDictId = dict.id"
              @mouseleave="hoveredDictId = undefined"
              @click="onDictSelect(dict.id)"
            >
              <!-- 上半部分：字典名称和操作按钮 -->
              <div class="mb-1 flex min-h-6 items-center justify-between">
                <div
                  class="flex min-w-0 flex-1 items-center justify-between gap-1"
                >
                  <div class="truncate text-sm font-medium" :title="dict.name">
                    {{ dict.name }}
                  </div>
                  <ElTag
                    v-if="dict.is_global"
                    size="small"
                    type="warning"
                    class="flex-shrink-0"
                  >
                    {{ $t('dict.globalTag') }}
                  </ElTag>
                </div>

                <!-- 操作图标 -->
                <div
                  v-if="hoveredDictId === dict.id"
                  class="ml-2 flex flex-shrink-0 gap-0.5"
                  @click.stop
                >
                  <ElTooltip :content="$t('dict.edit')" placement="top">
                    <ElButton
                      type="primary"
                      text
                      size="small"
                      circle
                      @click="onEditDict(dict, $event)"
                    >
                      <IconifyIcon icon="ep:edit" class="size-4" />
                    </ElButton>
                  </ElTooltip>
                  <ElButton
                    type="danger"
                    text
                    size="small"
                    circle
                    style="margin-left: 0"
                    :title="$t('common.delete')"
                    @click="onDeleteDict(dict, $event)"
                  >
                    <IconifyIcon icon="ep:delete" class="size-4" />
                  </ElButton>
                </div>
              </div>

              <!-- 下半部分：详细信息 -->
              <div class="flex items-center gap-2 text-xs opacity-70">
                <!-- 字典编码 -->
                <span class="truncate" :title="dict.code">
                  {{ dict.code }}
                </span>

                <!-- 应用名称 -->
                <span class="text-gray-400">|</span>
                <span
                  class="truncate"
                  :title="dict.application_name || $t('dict.mainApp')"
                >
                  {{ dict.application_name || $t('dict.mainApp') }}
                </span>
                <!-- 分隔符 -->
                <span class="text-gray-400">|</span>

                <!-- 状态 -->
                <span v-if="dict.status" class="flex-shrink-0">
                  {{ $t('common.enabled') }}
                </span>
                <span v-else class="flex-shrink-0">
                  {{ $t('common.disabled') }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </ElSkeleton>
    </div>
  </ElCard>
</template>

<style scoped>
/* 输入框前置图标样式 */
:deep(.el-input__icon) {
  cursor: pointer;
}

/* 文本按钮样式 */
:deep(.el-button--text) {
  padding: 0 4px;
}

/* 骨架屏样式 */
.dict-skeleton-item {
  box-sizing: border-box;
  width: 100%;
  padding: 8px 12px;
}

/* 字典项样式 */
.dict-item {
  min-height: 56px;
}
</style>
