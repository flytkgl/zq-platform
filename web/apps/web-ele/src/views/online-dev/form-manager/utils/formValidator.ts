import { $t } from '@vben/locales';

export interface ValidationError {
  type: 'error' | 'warning';
  message: string;
  component?: string;
  category?: string; // 错误分类：form, list, subTable, query 等
}

/**
 * 校验表单配置
 * @param items 表单设计器中的组件列表
 * @param tableConfigs 数据表配置列表
 */
export function validateFormConfig(
  items: any[],
  tableConfigs: any[],
): ValidationError[] {
  const errors: ValidationError[] = [];

  // 1. 非空校验
  if (!items || items.length === 0) {
    // 这通常在外部判断，但这里也可以作为一条规则
    // errors.push({ type: 'warning', message: '表单组件为空', component: '全局' });
    return errors;
  }

  // 构建合法字段集
  const validFields = new Set<string>();
  const subTableFields = new Map<string, Set<string>>();

  tableConfigs.forEach((table) => {
    if (table.type === 'main') {
      table.fields.forEach((f: any) => validFields.add(f.name));
    } else {
      const subFields = new Set<string>();
      table.fields.forEach((f: any) => subFields.add(f.name));
      subTableFields.set(table.tableName, subFields);
    }
  });

  // 提取所有组件（带上下文信息）
  interface ComponentWithContext {
    component: any;
    parentSubTable?: string; // 所属子表单的表名
  }
  const allComponents: ComponentWithContext[] = [];

  const traverse = (list: any[], parentSubTable?: string) => {
    list.forEach((item) => {
      allComponents.push({ component: item, parentSubTable });

      // 如果是子表单，其 children 属于该子表单
      if (item.type === 'sub-table' && item.children) {
        traverse(item.children, item.field); // item.field 是表名
      } else {
        if (item.children) traverse(item.children, parentSubTable);
      }

      if (item.columns) {
        item.columns.forEach((col: any) => {
          if (col.children) traverse(col.children, parentSubTable);
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) traverse(subItem.children, parentSubTable);
        });
      }
    });
  };
  traverse(items);

  // 2. 详细校验
  // 分别记录主表和各从表已使用的字段
  const usedMainFields = new Set<string>();
  const usedSubTableFields = new Map<string, Set<string>>();
  const layoutTypes = new Set([
    'alert',
    'collapse',
    'divider',
    'grid',
    'html',
    'spacer',
    'steps',
    'tabs',
    'text',
    'timeline',
    'title',
  ]); // 不需要字段名的布局/展示组件

  for (const { component: comp, parentSubTable } of allComponents) {
    // 跳过布局组件
    if (layoutTypes.has(comp.type)) continue;

    const compName = comp.label || comp.type;

    // 2.1 未绑定字段校验
    if (!comp.field) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.notBound'),
        component: compName,
      });
      continue;
    }

    // 2.2 重复字段校验（区分主表和从表）
    if (parentSubTable) {
      // 从表内的字段
      if (!usedSubTableFields.has(parentSubTable)) {
        usedSubTableFields.set(parentSubTable, new Set());
      }
      const subFields = usedSubTableFields.get(parentSubTable)!;
      if (subFields.has(comp.field)) {
        errors.push({
          type: 'warning',
          message: $t('form-manager.validator.duplicateSubField', {
            table: parentSubTable,
            field: comp.field,
          }),
          component: compName,
        });
      }
      subFields.add(comp.field);
    } else {
      // 主表字段或子表单组件本身
      if (usedMainFields.has(comp.field)) {
        errors.push({
          type: 'warning',
          message: $t('form-manager.validator.duplicateField', {
            field: comp.field,
          }),
          component: compName,
        });
      }
      usedMainFields.add(comp.field);
    }

    // 2.3 非法字段校验 (必须在数据表中存在，虚拟字段跳过)
    const isVirtualField = comp.props?.isVirtualField === true;
    if (isVirtualField) {
      // 虚拟字段不对应数据库列，跳过字段存在性和类型校验
      continue;
    }
    if (comp.type === 'sub-table') {
      // 从表组件校验
      if (!subTableFields.has(comp.field)) {
        errors.push({
          type: 'error',
          message: $t('form-manager.validator.invalidSubTable', {
            table: comp.field,
          }),
          component: compName,
        });
      }
    } else if (parentSubTable) {
      // 从表内的字段，检查是否在对应从表的字段列表中
      const subFields = subTableFields.get(parentSubTable);
      if (!subFields || !subFields.has(comp.field)) {
        errors.push({
          type: 'error',
          message: $t('form-manager.validator.fieldNotInSubTable', {
            field: comp.field,
            table: parentSubTable,
          }),
          component: compName,
        });
      }
    } else {
      // 主表字段，检查是否在主表字段列表中
      if (!validFields.has(comp.field)) {
        errors.push({
          type: 'error',
          message: $t('form-manager.validator.fieldNotInMainTable', {
            field: comp.field,
          }),
          component: compName,
        });
      }
    }

    // 2.4 文件选择和图片组件的数据库类型校验
    if (['file-selector', 'image-selector'].includes(comp.type)) {
      // 获取字段的数据库类型
      let fieldType = '';

      if (parentSubTable) {
        // 从表字段
        const table = tableConfigs.find((t) => t.tableName === parentSubTable);
        const field = table?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toUpperCase() || '';
      } else {
        // 主表字段
        const mainTable = tableConfigs.find((t) => t.type === 'main');
        const field = mainTable?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toUpperCase() || '';
      }

      // 判断是否多选
      const isMultiple = comp.props?.multiple === true;

      if (isMultiple) {
        // 多选必须是 JSON 类型
        if (fieldType !== 'JSON' && fieldType !== 'JSONB') {
          errors.push({
            type: 'error',
            message: $t('form-manager.validator.fileMultipleRequiresJson', {
              field: comp.field,
              currentType: fieldType || $t('form-manager.validator.unknown'),
            }),
            component: compName,
          });
        }
      } else {
        // 单选必须是 VARCHAR 类型
        const isVarcharType =
          fieldType.includes('VARCHAR') ||
          fieldType.includes('CHAR') ||
          fieldType.includes('STRING');

        if (!isVarcharType) {
          errors.push({
            type: 'error',
            message: $t('form-manager.validator.fileSingleRequiresVarchar', {
              field: comp.field,
              currentType: fieldType || $t('form-manager.validator.unknown'),
            }),
            component: compName,
          });
        }
      }
    }

    // 2.5 省市区组件的数据库类型校验
    if (comp.type === 'region-selector') {
      // 获取字段的数据库类型
      let fieldType = '';

      if (parentSubTable) {
        // 从表字段
        const table = tableConfigs.find((t) => t.tableName === parentSubTable);
        const field = table?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toUpperCase() || '';
      } else {
        // 主表字段
        const mainTable = tableConfigs.find((t) => t.type === 'main');
        const field = mainTable?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toUpperCase() || '';
      }

      // 省市区组件必须是 JSON 类型（存储完整路径数组）
      if (fieldType !== 'JSON' && fieldType !== 'JSONB') {
        errors.push({
          type: 'error',
          message: $t('form-manager.validator.regionRequiresJson', {
            field: comp.field,
            currentType: fieldType || $t('form-manager.validator.unknown'),
          }),
          component: compName,
        });
      }
    }

    // 2.6 数字类型字段与组件类型匹配校验
    {
      // 获取字段的数据库类型
      let fieldType = '';

      if (parentSubTable) {
        // 从表字段
        const table = tableConfigs.find((t) => t.tableName === parentSubTable);
        const field = table?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toLowerCase() || '';
      } else {
        // 主表字段
        const mainTable = tableConfigs.find((t) => t.type === 'main');
        const field = mainTable?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toLowerCase() || '';
      }

      // 判断是否为数字类型字段
      const isNumericField =
        fieldType.includes('int') ||
        fieldType.includes('decimal') ||
        fieldType.includes('numeric') ||
        fieldType.includes('float') ||
        fieldType.includes('double') ||
        fieldType.includes('real') ||
        fieldType.includes('money');

      // 非数字类型组件列表（文本、选择等）
      const nonNumericComponents = [
        'input',
        'textarea',
        'select',
        'radio',
        'checkbox',
        'cascader',
        'tree-select',
        'date-picker',
        'time-picker',
        'time-select',
        'color-picker',
        'switch',
        'file-selector',
        'image-selector',
        'region-selector',
        'user-selector',
        'dept-selector',
        'post-selector',
        'role-selector',
        'table-selector',
        'linked-field',
        'current-user',
        'current-datetime',
        'code-generator',
        'ai-image-ocr',
      ];

      if (isNumericField && nonNumericComponents.includes(comp.type)) {
        errors.push({
          type: 'error',
          message: $t(
            'form-manager.validator.numericFieldRequiresNumericComponent',
            {
              field: comp.field,
              fieldType: fieldType.toUpperCase(),
              componentType: comp.type,
            },
          ),
          component: compName,
        });
      }
    }

    // 2.7 字段类型与组件类型匹配校验
    {
      // 获取字段的数据库类型
      let fieldType = '';

      if (parentSubTable) {
        // 从表字段
        const table = tableConfigs.find((t) => t.tableName === parentSubTable);
        const field = table?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toLowerCase() || '';
      } else {
        // 主表字段
        const mainTable = tableConfigs.find((t) => t.type === 'main');
        const field = mainTable?.fields.find((f: any) => f.name === comp.field);
        fieldType = field?.type?.toLowerCase() || '';
      }

      if (!fieldType) continue; // 跳过未知类型

      // 判断字段类型类别
      const isStringField =
        fieldType.includes('varchar') ||
        fieldType.includes('char') ||
        fieldType.includes('text') ||
        fieldType.includes('string');

      const isDateTimeField =
        fieldType.includes('timestamp') ||
        fieldType.includes('datetime') ||
        fieldType.includes('date') ||
        fieldType.includes('time');

      const isBooleanField =
        fieldType.includes('bool') || fieldType.includes('boolean');

      const isJsonField =
        fieldType.includes('json') || fieldType.includes('jsonb');

      // 日期时间相关组件
      const dateTimeComponents = ['date', 'time', 'current-datetime'];

      // 布尔相关组件
      const booleanComponents = ['switch'];

      // 字符串类型字段不能使用日期时间组件
      if (isStringField && dateTimeComponents.includes(comp.type)) {
        errors.push({
          type: 'error',
          message: $t(
            'form-manager.validator.stringFieldCannotUseDateComponent',
            {
              field: comp.field,
              fieldType: fieldType.toUpperCase(),
              componentType: comp.type,
            },
          ),
          component: compName,
        });
      }

      // 日期时间类型字段只能使用日期时间组件或文本组件
      const allowedForDateTimeField = [
        ...dateTimeComponents,
        'input',
        'textarea',
        'linked-field',
      ];
      if (isDateTimeField && !allowedForDateTimeField.includes(comp.type)) {
        errors.push({
          type: 'error',
          message: $t(
            'form-manager.validator.dateTimeFieldRequiresDateComponent',
            {
              field: comp.field,
              fieldType: fieldType.toUpperCase(),
              componentType: comp.type,
            },
          ),
          component: compName,
        });
      }

      // 布尔类型字段只能使用开关组件或文本组件
      const allowedForBooleanField = [
        ...booleanComponents,
        'input',
        'select',
        'radio',
        'linked-field',
      ];
      if (isBooleanField && !allowedForBooleanField.includes(comp.type)) {
        errors.push({
          type: 'error',
          message: $t(
            'form-manager.validator.booleanFieldRequiresSwitchComponent',
            {
              field: comp.field,
              fieldType: fieldType.toUpperCase(),
              componentType: comp.type,
            },
          ),
          component: compName,
        });
      }

      // JSON 类型字段只能使用特定组件
      const allowedForJsonField = [
        'checkbox',
        'cascader',
        'tree-select',
        'region-selector',
        'file-selector',
        'image-selector',
        'sub-table',
        'textarea',
        'input',
        'linked-field',
        'table-selector',
        'user-selector',
        'dept-selector',
        'post-selector',
        'role-selector',
      ];
      if (isJsonField && !allowedForJsonField.includes(comp.type)) {
        errors.push({
          type: 'error',
          message: $t('form-manager.validator.jsonFieldRequiresJsonComponent', {
            field: comp.field,
            fieldType: fieldType.toUpperCase(),
            componentType: comp.type,
          }),
          component: compName,
        });
      }
    }
  }

  return errors;
}

/**
 * 保存前的整体校验
 * @param formConfig 表单配置（包含 items）
 * @param tableConfigs 数据表配置列表
 * @param listConfig 列表设计配置
 * @param formFields 提取的表单字段列表
 */
export function validateBeforeSave(
  formConfig: { items: any[] },
  tableConfigs: any[],
  listConfig: any,
  formFields: any[],
): ValidationError[] {
  const errors: ValidationError[] = [];

  // 1. 先执行表单配置校验
  const formErrors = validateFormConfig(formConfig.items, tableConfigs);
  formErrors.forEach((e) => {
    e.category = 'form';
    errors.push(e);
  });

  // 2. 校验列表设计中的列配置
  const columnErrors = validateListColumns(
    listConfig,
    formFields,
    tableConfigs,
  );
  errors.push(...columnErrors);

  // 3. 校验查询字段配置
  const queryErrors = validateQueryFields(listConfig, formFields, tableConfigs);
  errors.push(...queryErrors);

  // 4. 校验子表按钮配置
  const subTableErrors = validateSubTableButtons(listConfig, tableConfigs);
  errors.push(...subTableErrors);

  // 5. 校验自定义按钮配置
  const customButtonErrors = validateCustomButtons(listConfig);
  errors.push(...customButtonErrors);

  return errors;
}

/**
 * 校验列表列配置
 */
function validateListColumns(
  listConfig: any,
  formFields: any[],
  tableConfigs: any[],
): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!listConfig?.columns || !Array.isArray(listConfig.columns)) {
    return errors;
  }

  // 构建有效字段集合（表单字段 + 数据库字段）
  const validFields = new Set<string>();
  formFields.forEach((f) => {
    if (f.field) validFields.add(f.field);
  });

  // 添加数据库中的所有字段（包括系统字段）
  const mainTable = tableConfigs.find((t: any) => t.type === 'main');
  if (mainTable?.fields) {
    mainTable.fields.forEach((f: any) => {
      if (f.name) validFields.add(f.name);
    });
  }

  // 调试日志
  console.log('[validateListColumns] validFields:', [...validFields]);
  console.log(
    '[validateListColumns] columns:',
    listConfig.columns.map((c: any) => c.field),
  );

  // 校验每个列配置
  listConfig.columns.forEach((col: any) => {
    if (!col.field) {
      errors.push({
        type: 'warning',
        message: $t('form-manager.validator.columnNoField'),
        component:
          col.label || col.title || $t('form-manager.validator.unknownColumn'),
        category: 'list',
      });
      return;
    }

    // 检查字段是否存在
    if (!validFields.has(col.field)) {
      console.log('[validateListColumns] Field not found:', col.field);
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.columnFieldNotExist', {
          field: col.field,
        }),
        component: col.label || col.title || col.field,
        category: 'list',
      });
    }
  });

  return errors;
}

/**
 * 校验查询字段配置
 */
function validateQueryFields(
  listConfig: any,
  formFields: any[],
  tableConfigs: any[],
): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!listConfig?.queryFields || !Array.isArray(listConfig.queryFields)) {
    return errors;
  }

  // 构建有效字段集合
  const validFields = new Set<string>();
  formFields.forEach((f) => {
    if (f.field) validFields.add(f.field);
  });

  // 添加数据库中的所有字段
  const mainTable = tableConfigs.find((t: any) => t.type === 'main');
  if (mainTable?.fields) {
    mainTable.fields.forEach((f: any) => {
      if (f.name) validFields.add(f.name);
    });
  }

  // 调试日志
  console.log('[validateQueryFields] validFields:', [...validFields]);
  console.log(
    '[validateQueryFields] queryFields:',
    listConfig.queryFields.map((q: any) => q.field),
  );

  // 校验每个查询字段
  listConfig.queryFields.forEach((qf: any) => {
    if (!qf.field) {
      errors.push({
        type: 'warning',
        message: $t('form-manager.validator.queryFieldNoField'),
        component: qf.label || $t('form-manager.validator.unknownQueryField'),
        category: 'query',
      });
      return;
    }

    // 检查字段是否存在
    if (!validFields.has(qf.field)) {
      console.log('[validateQueryFields] Field not found:', qf.field);
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.queryFieldNotExist', {
          field: qf.field,
        }),
        component: qf.label || qf.field,
        category: 'query',
      });
    }
  });

  return errors;
}

/**
 * 校验子表按钮配置
 */
function validateSubTableButtons(
  listConfig: any,
  tableConfigs: any[],
): ValidationError[] {
  const errors: ValidationError[] = [];

  if (
    !listConfig?.subTableButtons ||
    !Array.isArray(listConfig.subTableButtons)
  ) {
    return errors;
  }

  // 获取配置的子表列表
  const configuredSubTables = new Set<string>();
  tableConfigs
    .filter((t: any) => t.type === 'sub')
    .forEach((t: any) => configuredSubTables.add(t.tableName));

  listConfig.subTableButtons.forEach((btn: any, index: number) => {
    const btnName =
      btn.buttonText ||
      `${$t('form-manager.validator.subTableButton')} ${index + 1}`;

    // 校验按钮文本
    if (!btn.buttonText) {
      errors.push({
        type: 'warning',
        message: $t('form-manager.validator.subTableButtonNoText'),
        component: btnName,
        category: 'subTable',
      });
    }

    // 校验子表单编码
    if (!btn.subFormCode) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.subTableButtonNoFormCode'),
        component: btnName,
        category: 'subTable',
      });
    }

    // 校验外键字段
    if (!btn.foreignKeyField) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.subTableButtonNoForeignKey'),
        component: btnName,
        category: 'subTable',
      });
    }
  });

  return errors;
}

/**
 * 校验自定义按钮配置
 */
function validateCustomButtons(listConfig: any): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!listConfig?.customButtons || !Array.isArray(listConfig.customButtons)) {
    return errors;
  }

  listConfig.customButtons.forEach((btn: any, index: number) => {
    const btnName =
      btn.name || `${$t('form-manager.validator.customButton')} ${index + 1}`;

    // 校验按钮名称
    if (!btn.name) {
      errors.push({
        type: 'warning',
        message: $t('form-manager.validator.customButtonNoName'),
        component: btnName,
        category: 'customButton',
      });
    }

    // 校验操作类型配置
    if (btn.actionType === 'link' && !btn.actionConfig?.url) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.customButtonLinkNoUrl'),
        component: btnName,
        category: 'customButton',
      });
    }

    if (btn.actionType === 'api' && !btn.actionConfig?.apiUrl) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.customButtonApiNoUrl'),
        component: btnName,
        category: 'customButton',
      });
    }

    if (btn.actionType === 'event' && !btn.actionConfig?.eventName) {
      errors.push({
        type: 'error',
        message: $t('form-manager.validator.customButtonEventNoName'),
        component: btnName,
        category: 'customButton',
      });
    }
  });

  return errors;
}
