<script setup lang="ts">
import type { TableConfig, TableField } from '../store/formDesignStore';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import {
  ArrowDown,
  ArrowRight,
  Calendar,
  Document,
  Edit,
  Grid,
  Odometer,
  Open,
} from '@element-plus/icons-vue';
import { ElIcon, ElScrollbar, ElTag } from 'element-plus';
import { storeToRefs } from 'pinia';
import draggable from 'vuedraggable';

import { useFormDesignStore } from '../store/formDesignStore';

const props = defineProps<{
  searchKeyword?: string;
}>();

const store = useFormDesignStore();
const { dataSource, formConf } = storeToRefs(store);

// 折叠状态管理
const activeGroups = ref(['main']); // 默认展开主表

const toggleGroup = (group: string) => {
  const index = activeGroups.value.indexOf(group);
  if (index === -1) {
    activeGroups.value.push(group);
  } else {
    activeGroups.value.splice(index, 1);
  }
};

// 后端自动处理的系统字段（禁止拖拽，标注"自动处理"）
const AUTO_HANDLED_FIELDS = new Set([
  'sys_create_datetime',
  'sys_creator_id',
  'sys_dept_id',
  'sys_modifier_id',
  'sys_update_datetime',
]);

// 判断字段是否为自动处理字段
const isAutoHandledField = (fieldName: string) => {
  return AUTO_HANDLED_FIELDS.has(fieldName);
};

// 字段过滤函数
const filterFields = (fields: TableField[]) => {
  if (!props.searchKeyword) return fields;
  const keyword = props.searchKeyword.toLowerCase();
  return fields.filter(
    (field) =>
      field.name.toLowerCase().includes(keyword) ||
      (field.comment && field.comment.toLowerCase().includes(keyword)),
  );
};

// 计算已使用的主表字段集合（不在子表单内的字段）
const usedMainTableFields = computed(() => {
  const fields = new Set<string>();

  // 递归查找字段，但不进入子表单内部
  const findFields = (items: any[]) => {
    items.forEach((item) => {
      // 子表单的 field 是表名，不是主表字段，跳过
      if (item.type === 'sub-table') {
        // 不进入子表单内部
        return;
      }
      if (item.field) {
        fields.add(item.field);
      }
      if (item.children) findFields(item.children);
      if (item.columns) {
        item.columns.forEach((col: any) => {
          if (col.children) findFields(col.children);
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) findFields(subItem.children);
        });
      }
    });
  };

  findFields(formConf.value.items);
  return fields;
});

// 计算已使用的从表字段集合（按表名分组）
const usedSubTableFields = computed(() => {
  const tableFieldsMap = new Map<string, Set<string>>();

  // 递归查找子表单及其内部字段
  const findSubTableFields = (items: any[]) => {
    items.forEach((item) => {
      if (item.type === 'sub-table' && item.field) {
        const tableName = item.field;
        if (!tableFieldsMap.has(tableName)) {
          tableFieldsMap.set(tableName, new Set());
        }
        // 收集子表单内部的字段
        if (item.children) {
          item.children.forEach((child: any) => {
            if (child.field) {
              tableFieldsMap.get(tableName)!.add(child.field);
            }
          });
        }
      }
      // 继续递归查找嵌套的子表单
      if (item.columns) {
        item.columns.forEach((col: any) => {
          if (col.children) findSubTableFields(col.children);
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) findSubTableFields(subItem.children);
        });
      }
      if (item.children && item.type !== 'sub-table') {
        findSubTableFields(item.children);
      }
    });
  };

  findSubTableFields(formConf.value.items);
  return tableFieldsMap;
});

// 计算已使用的从表集合（通过子表单的 field 属性判断）
const usedSubTables = computed(() => {
  const tables = new Set<string>();

  const findSubTables = (items: any[]) => {
    items.forEach((item) => {
      if (item.type === 'sub-table' && item.field) {
        tables.add(item.field);
      }
      if (item.children) findSubTables(item.children);
      if (item.columns) {
        item.columns.forEach((col: any) => {
          if (col.children) findSubTables(col.children);
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) findSubTables(subItem.children);
        });
      }
    });
  };

  findSubTables(formConf.value.items);
  return tables;
});

// 判断字段是否已使用（区分主表和从表）
const isFieldUsed = (fieldName: string, tableName?: string) => {
  if (tableName) {
    // 从表字段：检查对应子表单内是否已使用
    const tableFields = usedSubTableFields.value.get(tableName);
    return tableFields ? tableFields.has(fieldName) : false;
  } else {
    // 主表字段：检查主表单中是否已使用
    return usedMainTableFields.value.has(fieldName);
  }
};

// 判断从表是否已使用
const isSubTableUsed = (tableName: string) =>
  usedSubTables.value.has(tableName);

// 拖拽事件处理
const onDragStart = () => store.setDragging(true);
const onDragEnd = () => store.setDragging(false);

// 点击添加字段到画布（仅主表字段可点击添加）
const handleClickAdd = (field: TableField, isSubTable = false) => {
  // 从表字段不允许点击添加，只能拖入子表单
  if (isSubTable) return;

  if (isFieldUsed(field.name)) return;

  const component = generateComponentFromField(field);
  store.addComponent(component);
};

// 点击添加从表（子表单）到画布
const handleClickAddSubTable = (table: TableConfig) => {
  if (isSubTableUsed(table.tableName)) return;

  const component = generateSubTableFromTable(table);
  store.addComponent(component);
};

// 根据字段类型映射组件类型和图标
const getComponentTypeInfo = (fieldType: string) => {
  const type = fieldType.toLowerCase();

  if (
    type.includes('int') ||
    type.includes('decimal') ||
    type.includes('numeric') ||
    type.includes('float') ||
    type.includes('double')
  ) {
    return { type: 'input-number', icon: Odometer, label: $t('form-design.material.components.number') };
  }
  if (
    type.includes('datetime') ||
    type.includes('timestamp') ||
    type.includes('date')
  ) {
    return { type: 'date', icon: Calendar, label: $t('form-design.material.components.date') };
  }
  if (type.includes('text') || type.includes('long') || type.includes('blob')) {
    return { type: 'textarea', icon: Document, label: $t('form-design.material.components.textarea') };
  }
  if (type.includes('bool') || type.includes('tinyint(1)')) {
    return { type: 'switch', icon: Open, label: $t('form-design.material.components.switch') };
  }
  if (type.includes('char') || type.includes('string')) {
    return { type: 'input', icon: Edit, label: $t('form-design.material.components.input') };
  }

  // 默认
  return { type: 'input', icon: Edit, label: $t('form-design.material.components.input') };
};

// 生成组件配置
// 判断字段是否为系统字段（主键、ID、外键）
const isSystemField = (field: TableField, foreignKey?: string) => {
  return (
    field.isPrimaryKey ||
    field.name.toLowerCase() === 'id' ||
    (foreignKey && field.name === foreignKey)
  );
};

const generateComponentFromField = (field: TableField, foreignKey?: string) => {
  const { type } = getComponentTypeInfo(field.type);

  // 判断是否为系统字段（主键、ID、外键），系统字段默认禁用
  const isSystem = isSystemField(field, foreignKey);

  // 根据数据库约束生成校验规则
  const regList: { message: string; pattern: string }[] = [];

  // 字符串类型的最大长度校验
  if (field.maxLength && field.maxLength > 0) {
    // 使用正则限制最大长度
    regList.push({
      pattern: `^.{0,${field.maxLength}}$`,
      message: $t('form-design.attribute.maxLenError', { max: field.maxLength }),
    });
  }

  // 整数类型校验
  const fieldType = field.type.toLowerCase();
  if (fieldType.includes('int') && !fieldType.includes('point')) {
    regList.push({
      pattern: String.raw`^-?\d+$`,
      message: $t('form-design.attribute.integerError'),
    });
  }

  // 数值类型精度校验
  if (field.precision && field.scale !== undefined && field.scale > 0) {
    const integerPart = field.precision - field.scale;
    regList.push({
      pattern: `^-?\\d{0,${integerPart}}(\\.\\d{0,${field.scale}})?$`,
      message: $t('form-design.attribute.numberPrecisionError', {
        integer: integerPart,
        scale: field.scale,
      }),
    });
  }

  const baseComponent: any = {
    type,
    label: field.comment || field.name, // 优先使用注释作为标签
    field: field.name, // 自动绑定字段名
    props: {
      placeholder: isSystem
        ? $t('form-design.attribute.systemAutoGenerate')
        : (['cascader', 'checkbox', 'color', 'cron-selector', 'date', 'dept-selector', 'file-selector', 'form-selector', 'image-selector', 'post-selector', 'radio', 'rate', 'region-selector', 'role-selector', 'select', 'slider', 'table-selector', 'time', 'tree-select', 'user-selector'].includes(type)
          ? $t('common.selectPlaceholder') + (field.comment || field.name)
          : $t('common.placeholder') + (field.comment || field.name)),
      width: '100%',
      disabled: isSystem, // 系统字段默认禁用
      // NOT NULL -> required: true，但系统字段不需要必填
      required: !field.nullable && !field.isPrimaryKey && !isSystem,
    },
    // 添加正则校验规则
    regList: regList.length > 0 ? regList : undefined,
    // 标记是否为系统字段
    isSystemField: isSystem,
  };

  // 根据类型补充特定属性
  switch (type) {
    case 'date': {
      Object.assign(baseComponent.props, {
        type: 'date',
        format: 'YYYY-MM-DD',
        valueFormat: 'YYYY-MM-DD',
      });

      break;
    }
    case 'input': {
      // input 默认显示字数限制
      baseComponent.props.showWordLimit = true;
      // input 添加 maxlength 属性
      if (field.maxLength) {
        baseComponent.props.maxlength = field.maxLength;
      }

      break;
    }
    case 'input-number': {
      Object.assign(baseComponent.props, {
        controls: true,
        // 如果有精度信息，设置精度
        precision: field.scale,
      });

      break;
    }
    case 'switch': {
      Object.assign(baseComponent.props, { width: 40 });

      break;
    }
    case 'textarea': {
      Object.assign(baseComponent.props, { type: 'textarea', rows: 3 });
      // textarea 默认显示字数限制
      baseComponent.props.showWordLimit = true;
      // textarea 添加 maxlength 属性
      if (field.maxLength) {
        baseComponent.props.maxlength = field.maxLength;
      }

      break;
    }
    // No default
  }

  return store.cloneComponent(baseComponent);
};

// 系统字段列表（不添加到子表单中）
const SYSTEM_FIELDS = new Set([
  'sys_create_datetime',
  'sys_creator_id',
  'sys_dept_id',
  'sys_modifier_id',
  'sys_update_datetime',
]);

// 根据从表配置生成子表单组件
const generateSubTableFromTable = (table: TableConfig) => {
  // 过滤掉系统字段，只保留业务字段（包括主键和外键，但设为禁用）
  const businessFields = table.fields.filter(
    (field) => !SYSTEM_FIELDS.has(field.name),
  );

  // 生成子表单的子组件
  const children = businessFields.map((field) => {
    // 判断是否为系统字段
    const isSystem = isSystemField(field, table.foreignKey);
    const { type } = getComponentTypeInfo(field.type);

    // 根据数据库约束生成校验规则
    const regList: { message: string; pattern: string }[] = [];

    // 字符串类型的最大长度校验
    if (field.maxLength && field.maxLength > 0) {
      regList.push({
        pattern: `^.{0,${field.maxLength}}$`,
        message: $t('form-design.attribute.maxLenError', { max: field.maxLength }),
      });
    }

    // 整数类型校验
    const fieldType = field.type.toLowerCase();
    if (fieldType.includes('int') && !fieldType.includes('point')) {
      regList.push({
        pattern: String.raw`^-?\d+$`,
        message: $t('form-design.attribute.integerError'),
      });
    }

    // 数值类型精度校验
    if (field.precision && field.scale !== undefined && field.scale > 0) {
      const integerPart = field.precision - field.scale;
      regList.push({
        pattern: `^-?\\d{0,${integerPart}}(\\.\\d{0,${field.scale}})?$`,
        message: $t('form-design.attribute.numberPrecisionError', {
          integer: integerPart,
          scale: field.scale,
        }),
      });
    }

    const component: any = {
      type,
      label: field.comment || field.name,
      field: field.name,
      props: {
        placeholder: isSystem
          ? $t('form-design.attribute.systemAutoGenerate')
          : $t('common.placeholder') + (field.comment || field.name),
        width: '100%',
        disabled: isSystem, // 系统字段默认禁用
        required: !field.nullable && !isSystem, // 系统字段不需要必填
      },
      regList: regList.length > 0 ? regList : undefined,
      isSystemField: isSystem, // 标记是否为系统字段
    };

    // 根据类型补充特定属性
    if (type === 'input-number' && field.scale !== undefined) {
      component.props.precision = field.scale;
    }
    if (type === 'input' || type === 'textarea') {
      // 默认显示字数限制
      component.props.showWordLimit = true;
      if (field.maxLength) {
        component.props.maxlength = field.maxLength;
      }
    }

    return component;
  });

  const subTableComponent = {
    type: 'sub-table',
    label: table.alias || table.tableName,
    field: table.tableName, // 使用表名作为字段标识
    props: {
      showIndex: true,
      summary: false,
      addable: true,
      deletable: true,
      displayMode: 'table',
    },
    children,
  };

  return store.cloneComponent(subTableComponent);
};

// Clone 函数：包装 generateComponentFromField
const cloneField = (field: TableField) => {
  return generateComponentFromField(field);
};

// Clone 函数：包装 generateSubTableFromTable
const cloneSubTable = (table: TableConfig) => {
  return generateSubTableFromTable(table);
};

// 包装主表字段（带过滤，但保留主键和ID字段）
const filteredMainTableFields = computed(() => {
  const fields = dataSource.value.mainTable?.fields || [];
  // 不再过滤主键和ID字段，让它们可以被添加（但会被设为禁用）
  return filterFields(fields);
});

// 包装从表列表（带过滤，但保留主键、ID和外键字段）
const filteredSubTables = computed(() => {
  if (!dataSource.value.subTables) return [];

  return dataSource.value.subTables
    .map((subTable) => {
      // 不再过滤主键、ID和外键字段，让它们可以被添加（但会被设为禁用）
      const filteredFields = filterFields(subTable.fields);

      // 如果从表名字匹配，或者有字段匹配，则显示该从表
      const subTableMatch =
        props.searchKeyword &&
        subTable.tableName
          .toLowerCase()
          .includes(props.searchKeyword.toLowerCase());

      if (!props.searchKeyword || subTableMatch || filteredFields.length > 0) {
        return {
          ...subTable,
          // 如果是表名匹配，显示所有字段；否则只显示匹配的字段
          fields:
            props.searchKeyword && subTableMatch
              ? subTable.fields
              : filteredFields,
        };
      }
      return null;
    })
    .filter(Boolean) as TableConfig[];
});
</script>

<template>
  <div class="h-full">
    <ElScrollbar class="h-full">
      <div class="px-4 pb-4">
        <!-- 主表字段 -->
        <div class="component-group mb-4">
          <div
            class="group-title mb-2 flex cursor-pointer select-none items-center justify-between text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
            @click="toggleGroup('main')"
          >
            <span class="font-bold">{{ $t('form-design.attribute.mainTableFields') }} ({{
                dataSource.mainTable?.tableName || $t('form-design.attribute.notConfigured')
              }})</span>
            <ElIcon class="h-4 w-4">
              <ArrowDown v-if="activeGroups.includes('main')" />
              <ArrowRight v-else />
            </ElIcon>
          </div>

          <div v-show="activeGroups.includes('main')">
            <div
              v-if="!dataSource.mainTable"
              class="rounded bg-[var(--el-fill-color-light)] py-4 text-center text-xs text-[var(--el-text-color-placeholder)]"
            >
              {{ $t('form-design.attribute.configDataSourceTip') }}
            </div>

            <div
              v-else-if="filteredMainTableFields.length === 0"
              class="rounded bg-[var(--el-fill-color-light)] py-2 text-center text-xs text-[var(--el-text-color-placeholder)]"
            >
              {{ $t('form-design.material.noFields') }}
            </div>

            <draggable
              v-else
              :list="filteredMainTableFields"
              :group="{ name: 'form-design', pull: 'clone', put: false }"
              :sort="false"
              :clone="cloneField"
              item-key="name"
              class="grid grid-cols-1 gap-2"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element }">
                <div
                  class="component-item flex cursor-move items-center justify-between rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] px-3 py-2 transition-colors hover:border-[var(--el-color-primary)] hover:text-[var(--el-color-primary)]"
                  :class="{
                    'cursor-not-allowed opacity-50 hover:!border-[var(--el-border-color)] hover:!text-inherit':
                      isFieldUsed(element.name) || isAutoHandledField(element.name),
                  }"
                  @click.stop="!isAutoHandledField(element.name) && handleClickAdd(element)"
                >
                  <div class="flex items-center gap-2 overflow-hidden">
                    <ElIcon class="flex-shrink-0 text-sm">
                      <component
                        :is="getComponentTypeInfo(element.type).icon"
                      />
                    </ElIcon>
                    <div class="flex flex-col overflow-hidden">
                      <span
                        class="truncate text-xs font-medium"
                        :title="element.name"
                      >
                        {{ element.name }}
                      </span>
                      <span
                        class="truncate text-[10px] text-[var(--el-text-color-secondary)]"
                        :title="element.comment"
                      >
                        {{ element.comment || '-' }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <ElTag
                      v-if="isAutoHandledField(element.name)"
                      size="small"
                      type="warning"
                      effect="light"
                      class="h-4 px-1 py-0 text-[10px]"
                    >
                      {{ $t('form-design.attribute.autoHandled') }}
                    </ElTag>
                    <ElTag
                      v-else-if="isFieldUsed(element.name)"
                      size="small"
                      type="info"
                      effect="light"
                      class="h-4 px-1 py-0 text-[10px]"
                    >
                      {{ $t('form-design.attribute.added') }}
                    </ElTag>
                    <template v-else>
                      <ElTag
                        v-if="element.isPrimaryKey"
                        size="small"
                        type="warning"
                        effect="plain"
                        class="h-4 px-1 py-0 text-[10px]"
                      >
                        PK
                      </ElTag>
                      <ElTag
                        v-else-if="element.name.toLowerCase() === 'id'"
                        size="small"
                        type="warning"
                        effect="plain"
                        <!-- class="h-4 px-1 py-0 text-[10px]" --
>
                      >
                        ID
                      </ElTag>
                      <span
                        v-else
                        class="text-[10px] text-[var(--el-text-color-placeholder)]"
                        >{{ element.type }}</span>
                    </template>
                  </div>
                </div>
              </template>
            </draggable>
          </div>
        </div>

        <!-- 从表字段 (遍历每个从表) -->
        <div
          v-for="subTable in filteredSubTables"
          :key="subTable.id"
          class="component-group mb-4"
        >
          <div
            class="group-title mb-2 flex cursor-pointer select-none items-center justify-between text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
            @click="toggleGroup(`sub_${subTable.id}`)"
          >
            <span class="font-bold">{{ $t('form-design.attribute.subTableLabel') }}: {{ subTable.tableName }}</span>
            <div class="flex items-center gap-2">
              <ElTag size="small" effect="plain" class="origin-right scale-90">
                {{ $t('form-design.attribute.subTableLabel') }}
              </ElTag>
              <ElIcon class="h-4 w-4">
                <ArrowDown v-if="activeGroups.includes(`sub_${subTable.id}`)" />
                <ArrowRight v-else />
              </ElIcon>
            </div>
          </div>

          <div v-show="activeGroups.includes(`sub_${subTable.id}`)">
            <!-- 从表整体拖拽卡片 -->
            <draggable
              :list="[subTable]"
              :group="{ name: 'form-design', pull: 'clone', put: false }"
              :sort="false"
              :clone="cloneSubTable"
              item-key="id"
              class="mb-2"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element }">
                <div
                  class="sub-table-card flex cursor-move items-center justify-between rounded border-2 border-dashed border-[var(--el-color-primary-light-5)] bg-[var(--el-color-primary-light-9)] px-3 py-2 transition-colors hover:border-[var(--el-color-primary)] hover:bg-[var(--el-color-primary-light-8)]"
                  :class="{
                    'cursor-not-allowed opacity-50 hover:!border-[var(--el-color-primary-light-5)] hover:!bg-[var(--el-color-primary-light-9)]':
                      isSubTableUsed(element.tableName),
                  }"
                  @click.stop="handleClickAddSubTable(element)"
                >
                  <div class="flex items-center gap-2">
                    <ElIcon class="text-[var(--el-color-primary)]">
                      <Grid />
                    </ElIcon>
                    <div class="flex flex-col">
                      <span
                        class="text-xs font-medium text-[var(--el-color-primary)]"
                      >
                        {{ $t('form-design.attribute.addSubTableWhole') }}
                      </span>
                      <span
                        class="text-[10px] text-[var(--el-text-color-secondary)]"
                      >
                        {{ $t('form-design.attribute.fieldCount', { count: element.fields.length }) }}
                      </span>
                    </div>
                  </div>
                  <ElTag
                    v-if="isSubTableUsed(element.tableName)"
                    size="small"
                    type="info"
                    effect="light"
                    class="h-4 px-1 py-0 text-[10px]"
                  >
                    {{ $t('form-design.attribute.added') }}
                  </ElTag>
                </div>
              </template>
            </draggable>

            <!-- 从表字段提示 -->
            <div
              v-if="!isSubTableUsed(subTable.tableName)"
              class="mb-2 rounded bg-[var(--el-color-warning-light-9)] px-2 py-1.5 text-[10px] text-[var(--el-color-warning)]"
            >
              {{ $t('form-design.attribute.addSubTableFirstTip') }}
            </div>

            <!-- 从表单个字段列表 -->
            <draggable
              :list="subTable.fields"
              :group="{ name: 'sub-table-fields', pull: 'clone', put: false }"
              :sort="false"
              :clone="cloneField"
              item-key="name"
              class="grid grid-cols-1 gap-2"
              :class="{ 'opacity-60': !isSubTableUsed(subTable.tableName) }"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element }">
                <div
                  class="component-item flex cursor-move items-center justify-between rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] px-3 py-2 transition-colors hover:border-[var(--el-color-primary)] hover:text-[var(--el-color-primary)]"
                  :class="{
                    'cursor-not-allowed opacity-50 hover:!border-[var(--el-border-color)] hover:!text-inherit':
                      isFieldUsed(element.name, subTable.tableName),
                  }"
                  @click.stop="handleClickAdd(element, true)"
                >
                  <div class="flex items-center gap-2 overflow-hidden">
                    <ElIcon class="flex-shrink-0 text-sm">
                      <component
                        :is="getComponentTypeInfo(element.type).icon"
                      />
                    </ElIcon>
                    <div class="flex flex-col overflow-hidden">
                      <span
                        class="truncate text-xs font-medium"
                        :title="element.name"
                      >
                        {{ element.name }}
                      </span>
                      <span
                        class="truncate text-[10px] text-[var(--el-text-color-secondary)]"
                        :title="element.comment"
                      >
                        {{ element.comment || '-' }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <ElTag
                      v-if="isFieldUsed(element.name, subTable.tableName)"
                      size="small"
                      type="info"
                      effect="light"
                      class="h-4 px-1 py-0 text-[10px]"
                    >
                      {{ $t('form-design.attribute.added') }}
                    </ElTag>
                    <template v-else>
                      <ElTag
                        v-if="element.isPrimaryKey"
                        size="small"
                        type="warning"
                        effect="plain"
                        class="h-4 px-1 py-0 text-[10px]"
                      >
                        PK
                      </ElTag>
                      <ElTag
                        v-else-if="element.name.toLowerCase() === 'id'"
                        size="small"
                        type="warning"
                        effect="plain"
                        class="h-4 px-1 py-0 text-[10px]"
                      >
                        ID
                      </ElTag>
                      <ElTag
                        v-else-if="element.name === subTable.foreignKey"
                        size="small"
                        type="danger"
                        effect="plain"
                        class="h-4 px-1 py-0 text-[10px]"
                      >
                        FK
                      </ElTag>
                      <span
                        v-else
                        class="text-[10px] text-[var(--el-text-color-placeholder)]"
                        >{{ element.type }}</span>
                    </template>
                  </div>
                </div>
              </template>
            </draggable>
          </div>
        </div>
      </div>
    </ElScrollbar>
  </div>
</template>

<style scoped>
.component-item {
  /* 优化拖拽时的样式 */
  user-select: none;
}
</style>
