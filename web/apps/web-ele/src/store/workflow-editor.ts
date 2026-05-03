import type { Edge, Node } from '@vue-flow/core';

import { computed, ref } from 'vue';

import { defineStore } from 'pinia';

export interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
}

export const useWorkflowEditorStore = defineStore('workflow-editor', () => {
  // 历史记录
  const history = ref<WorkflowState[]>([]);
  const historyIndex = ref(-1);
  const maxHistory = 50;

  // 是否正在执行撤销/重做操作
  const isUndoRedo = ref(false);

  // 当前工作流 ID
  const workflowId = ref<string>('');

  // 是否有未保存的更改
  const hasUnsavedChanges = ref(false);

  // 自动保存定时器
  let autoSaveTimer: null | ReturnType<typeof setTimeout> = null;

  // 计算属性
  const canUndo = computed(() => historyIndex.value > 0);
  const canRedo = computed(() => historyIndex.value < history.value.length - 1);
  const currentState = computed(
    () => history.value[historyIndex.value] || null,
  );

  // 初始化工作流
  function initWorkflow(id: string, initialState?: WorkflowState) {
    workflowId.value = id;
    history.value = [];
    historyIndex.value = -1;
    hasUnsavedChanges.value = false;

    if (initialState) {
      saveHistory(initialState);
    }
  }

  // 保存历史状态（带防抖）
  let saveDebounceTimer: null | ReturnType<typeof setTimeout> = null;

  function saveHistory(state: WorkflowState, immediate = false) {
    if (isUndoRedo.value) return;

    const doSave = () => {
      // 深拷贝状态
      const clonedState: WorkflowState = {
        nodes: JSON.parse(JSON.stringify(state.nodes)),
        edges: JSON.parse(JSON.stringify(state.edges)),
      };

      // 如果当前不在最新位置，删除后面的历史
      if (historyIndex.value < history.value.length - 1) {
        history.value = history.value.slice(0, historyIndex.value + 1);
      }

      // 检查是否与上一个状态相同（避免重复保存）
      const lastState = history.value[history.value.length - 1];
      if (lastState) {
        const isSame =
          JSON.stringify(lastState.nodes) ===
            JSON.stringify(clonedState.nodes) &&
          JSON.stringify(lastState.edges) === JSON.stringify(clonedState.edges);
        if (isSame) return;
      }

      history.value.push(clonedState);

      // 限制历史记录数量
      if (history.value.length > maxHistory) {
        history.value.shift();
      }

      historyIndex.value = history.value.length - 1;
      hasUnsavedChanges.value = true;
    };

    if (immediate) {
      doSave();
    } else {
      // 防抖：300ms 内的多次调用只执行最后一次
      if (saveDebounceTimer) {
        clearTimeout(saveDebounceTimer);
      }
      saveDebounceTimer = setTimeout(doSave, 300);
    }
  }

  // 撤销
  function undo(): null | WorkflowState {
    if (!canUndo.value) return null;

    isUndoRedo.value = true;
    historyIndex.value--;
    const state = history.value[historyIndex.value];

    // 延迟重置标志，避免恢复状态时触发 saveHistory
    setTimeout(() => {
      isUndoRedo.value = false;
    }, 100);

    return state ? JSON.parse(JSON.stringify(state)) : null;
  }

  // 重做
  function redo(): null | WorkflowState {
    if (!canRedo.value) return null;

    isUndoRedo.value = true;
    historyIndex.value++;
    const state = history.value[historyIndex.value];

    setTimeout(() => {
      isUndoRedo.value = false;
    }, 100);

    return state ? JSON.parse(JSON.stringify(state)) : null;
  }

  // 标记为已保存
  function markAsSaved() {
    hasUnsavedChanges.value = false;
  }

  // 清除历史
  function clearHistory() {
    history.value = [];
    historyIndex.value = -1;
  }

  // 设置自动保存回调
  function triggerAutoSave(callback: () => void, delay = 2000) {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }
    autoSaveTimer = setTimeout(() => {
      if (hasUnsavedChanges.value) {
        callback();
      }
    }, delay);
  }

  // 清理
  function cleanup() {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = null;
    }
    if (saveDebounceTimer) {
      clearTimeout(saveDebounceTimer);
      saveDebounceTimer = null;
    }
  }

  // 重置 store 状态
  function $reset() {
    history.value = [];
    historyIndex.value = -1;
    isUndoRedo.value = false;
    workflowId.value = '';
    hasUnsavedChanges.value = false;
    cleanup();
  }

  return {
    // 状态
    history,
    historyIndex,
    isUndoRedo,
    workflowId,
    hasUnsavedChanges,

    // 计算属性
    canUndo,
    canRedo,
    currentState,

    // 方法
    initWorkflow,
    saveHistory,
    undo,
    redo,
    markAsSaved,
    clearHistory,
    triggerAutoSave,
    cleanup,
    $reset,
  };
});
