<script setup lang="ts">
import { $t } from '@vben/locales';
import { nextTick, ref, watch } from 'vue';

import {
  ElButton,
  ElCollapse,
  ElCollapseItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElTree,
} from 'element-plus';

const props = defineProps<{
  data: any[];
  modelValue: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'confirm']);

const visible = ref(false);
const treeData = ref<any[]>([]);
const currentNode = ref<any>(null);
const treeRef = ref<InstanceType<typeof ElTree>>();

// 生成唯一ID，用于树组件追踪
const generateId = () => `_${Math.random().toString(36).slice(2, 11)}`;

// 递归处理数据，确保有 id 和 children
const processData = (items: any[]): any[] => {
  return items.map((item) => ({
    ...item,
    id: item.id || generateId(),
    children: item.children ? processData(item.children) : [],
  }));
};

// 递归清理数据，移除临时 id
const cleanData = (items: any[]): any[] => {
  return items.map((item) => {
    const { id, ...rest } = item;
    const newItem: any = { ...rest };
    if (newItem.children && newItem.children.length > 0) {
      newItem.children = cleanData(newItem.children);
    } else {
      delete newItem.children;
    }
    return newItem;
  });
};

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val;
    if (val) {
      // 深拷贝并处理数据
      treeData.value = processData(
        JSON.parse(JSON.stringify(props.data || [])),
      );
      currentNode.value = null;
    }
  },
);

watch(
  () => visible.value,
  (val) => {
    emit('update:modelValue', val);
  },
);

const handleNodeClick = (data: any) => {
  currentNode.value = data;
};

const addRootNode = () => {
  const newNode = {
    id: generateId(),
    label: $t('form-design.attribute.addOption'),
    value: 'new_option',
    children: [],
  };
  treeData.value.push(newNode);
  currentNode.value = newNode;
  nextTick(() => {
    treeRef.value?.setCurrentKey(newNode.id);
  });
};

const addChildNode = () => {
  if (!currentNode.value) return;
  const newNode = {
    id: generateId(),
    label: $t('form-design.attribute.addChild'),
    value: 'new_child',
    children: [],
  };
  if (!currentNode.value.children) {
    currentNode.value.children = [];
  }
  currentNode.value.children.push(newNode);
  // 自动展开父节点
  /* treeRef.value?.store.nodesMap[currentNode.value.id].expanded = true; */
};

const removeNode = () => {
  if (!currentNode.value) return;
  treeRef.value?.remove(currentNode.value);
  currentNode.value = null;
};

const allowDrop = () => {
  // 可以添加限制逻辑，目前允许任意拖拽
  return true;
};

const handleConfirm = () => {
  const result = cleanData(treeData.value);
  emit('confirm', result);
  visible.value = false;
};
</script>

<template>
  <ElDialog
    v-model="visible"
    :title="$t('form-design.attribute.dataSource')"
    width="800px"
    :close-on-click-modal="false"
    append-to-body
  >
    <div class="flex h-[500px] rounded border border-[var(--el-border-color)]">
      <!-- 左侧树形结构 -->
      <div class="flex w-1/2 flex-col border-r border-[var(--el-border-color)]">
        <div
          class="flex gap-2 border-b border-[var(--el-border-color-lighter)] p-2"
        >
          <ElButton type="primary" size="small" @click="addRootNode">
            {{ $t('form-design.attribute.addRoot') }}
          </ElButton>
          <ElButton size="small" :disabled="!currentNode" @click="addChildNode">
            {{ $t('form-design.attribute.addChild') }}
          </ElButton>
          <ElButton
            type="danger"
            size="small"
            :disabled="!currentNode"
            @click="removeNode"
          >
            {{ $t('form-design.delete') }}
          </ElButton>
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <ElTree
            ref="treeRef"
            :data="treeData"
            node-key="id"
            default-expand-all
            draggable
            :allow-drop="allowDrop"
            highlight-current
            :expand-on-click-node="false"
            @node-click="handleNodeClick"
          >
            <template #default="{ data }">
              <span class="custom-tree-node text-sm">
                <span>{{ data.label }}</span>
                <span
                  class="ml-2 text-xs text-[var(--el-text-color-secondary)]"
                  v-if="data.value"
                  >({{ data.value }})</span
                >
              </span>
            </template>
          </ElTree>
        </div>
      </div>

      <!-- 右侧节点编辑 -->
      <div class="flex w-1/2 flex-col bg-[var(--el-fill-color-light)]">
        <div class="p-4" v-if="currentNode">
          <div
            class="mb-4 border-b pb-2 font-bold text-[var(--el-text-color-primary)]"
          >
            {{ $t('form-design.attribute.nodeProps') }}
          </div>
          <ElForm label-position="top" size="small">
            <ElFormItem :label="$t('form-design.attribute.nodeLabel')">
              <ElInput v-model="currentNode.label" :placeholder="$t('common.placeholder')" />
            </ElFormItem>
            <ElFormItem :label="$t('form-design.attribute.nodeValue')">
              <ElInput v-model="currentNode.value" :placeholder="$t('common.placeholder')" />
            </ElFormItem>
          </ElForm>
        </div>
        <div
          v-else
          class="flex flex-1 items-center justify-center text-sm text-[var(--el-text-color-placeholder)]"
        >
          {{ $t('form-design.attribute.selectNodeTip') }}
        </div>
      </div>
    </div>

    <div class="mt-4">
      <ElCollapse>
        <ElCollapseItem :title="$t('form-design.attribute.viewJson')" name="json">
          <ElInput
            :model-value="JSON.stringify(treeData, null, 2)"
            type="textarea"
            :rows="6"
            readonly
          />
        </ElCollapseItem>
      </ElCollapse>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <ElButton @click="visible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" @click="handleConfirm">{{ $t('common.ok') }}</ElButton>
      </span>
    </template>
  </ElDialog>
</template>

<style scoped>
:deep(.el-tree-node__content) {
  height: 32px;
}
</style>
