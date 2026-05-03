import { unref } from 'vue';

/**
 * 表单数据处理 Hook
 * 封装数据的初始化、提取主表数据、提取子表数据等逻辑
 * @param formData 响应式表单数据对象 (reactive)
 */
export function useFormData(formData: Record<string, any>) {
  /**
   * 递归初始化表单数据
   * @param items 表单配置项列表
   */
  function initFormData(items: any[]) {
    if (!items || !Array.isArray(items)) return;

    items.forEach((item: any) => {
      // 处理容器组件
      switch (item.type) {
        case 'collapse': {
          item.items?.forEach((panel: any) => {
            initFormData(panel.children || []);
          });

          break;
        }
        case 'grid': {
          item.columns?.forEach((col: any) => {
            initFormData(col.children || []);
          });

          break;
        }
        case 'tabs': {
          item.items?.forEach((tab: any) => {
            initFormData(tab.children || []);
          });

          break;
        }
        // No default
      }

      // 处理字段组件
      if (item.field) {
        // 如果数据中已经存在该字段（可能是编辑回显），则跳过初始化
        // 注意：这里可能需要根据业务需求调整，比如强制重置
        // 目前逻辑是：如果formData中该key不存在（undefined），则初始化
        if (formData[item.field] !== undefined) {
          // 特殊处理：如果是子表，且需要保证结构正确，可以在这里做检查
          return;
        }

        // 根据类型初始化默认值（优先使用组件配置的 defaultValue）
        if (item.defaultValue !== undefined && item.defaultValue !== null) {
          formData[item.field] = item.type === 'checkbox' && !Array.isArray(item.defaultValue)
            ? [item.defaultValue]
            : item.defaultValue;
        } else if (item.type === 'checkbox') {
          formData[item.field] = [];
        } else if (['input-number', 'rate', 'slider'].includes(item.type)) {
          formData[item.field] = 0;
        } else if (item.type === 'switch') {
          formData[item.field] = false;
        } else if (item.type === 'sub-table') {
          formData[item.field] = [];
          // 至少添加一行（取 minRows 和 1 的较大值）
          const min = Math.max(item.props?.minRows || 0, 1);
          for (let i = 0; i < min; i++) {
            const newRow: any = {
              _id: `${Date.now()}_${Math.random()}`,
              _isEditing: true,
            };
            item.children?.forEach((col: any) => {
              if (col.defaultValue !== undefined && col.defaultValue !== null && col.defaultValue !== '') {
                newRow[col.field] = JSON.parse(JSON.stringify(col.defaultValue));
              } else if (col.props?.multiple) {
                newRow[col.field] = [];
              } else {
                newRow[col.field] = null;
              }
            });
            formData[item.field].push(newRow);
          }
        } else {
          formData[item.field] = null;
        }
      }
    });
  }

  /**
   * 提取子表数据
   * @param items 表单配置项列表
   * @returns 子表数据对象 { tableName: rows[] }
   */
  function extractSubTables(items: any[]): Record<string, any[]> {
    const subTables: Record<string, any[]> = {};

    function traverse(list: any[]) {
      if (!list) return;

      list.forEach((item) => {
        if (item.type === 'sub-table' && item.field) {
          const rows = formData[item.field] || [];
          // 移除临时 _id 字段
          subTables[item.field] = rows.map((row: any) => {
            const { _id, ...rest } = row;
            return rest;
          });
        }
        // 递归处理容器
        if (item.columns) {
          item.columns.forEach((col: any) => traverse(col.children || []));
        }
        if (item.items) {
          item.items.forEach((sub: any) => traverse(sub.children || []));
        }
        // grid 等容器直接有 children 的情况（视具体数据结构而定，这里根据原有逻辑调整）
        if (item.children && !['sub-table'].includes(item.type)) {
          traverse(item.children);
        }
      });
    }

    traverse(unref(items));
    return subTables;
  }

  /**
   * 提取主表数据（排除子表字段）
   * @param items 表单配置项列表
   * @returns 主表数据对象
   */
  function extractMainData(items: any[]): Record<string, any> {
    const subTableFields = new Set<string>();
    const virtualFields = new Set<string>();

    // 1. 找出所有子表字段名和虚拟字段名
    function findExcludedFields(list: any[]) {
      if (!list) return;

      list.forEach((item) => {
        if (item.type === 'sub-table' && item.field) {
          subTableFields.add(item.field);
        }
        if (item.field && item.props?.isVirtualField) {
          virtualFields.add(item.field);
        }
        if (item.columns) {
          item.columns.forEach((col: any) =>
            findExcludedFields(col.children || []),
          );
        }
        if (item.items) {
          item.items.forEach((sub: any) =>
            findExcludedFields(sub.children || []),
          );
        }
        if (item.children && !['sub-table'].includes(item.type)) {
          findExcludedFields(item.children);
        }
      });
    }

    findExcludedFields(unref(items));

    // 2. 过滤掉子表字段和虚拟字段，只保留主表字段
    // 将 undefined 转为 null，确保 JSON.stringify 不会丢失该字段
    const mainData: Record<string, any> = {};
    Object.keys(formData).forEach((key) => {
      if (!subTableFields.has(key) && !virtualFields.has(key)) {
        mainData[key] = formData[key] === undefined ? null : formData[key];
      }
    });

    return mainData;
  }

  /**
   * 重置表单数据
   */
  function resetFormData() {
    Object.keys(formData).forEach((key) => delete formData[key]);
  }

  return {
    initFormData,
    extractSubTables,
    extractMainData,
    resetFormData,
  };
}
