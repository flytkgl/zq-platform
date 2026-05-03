<script setup lang="ts">
import { computed, markRaw, ref, watch } from 'vue';

import { $t } from '@vben/locales';
import {
  ArrowDown,
  ArrowRight,
  Avatar,
  Calendar,
  CaretBottom,
  Check,
  CircleCheck,
  Clock,
  Connection,
  Document,
  Edit,
  Files,
  Folder,
  Grid,
  List,
  Location,
  MagicStick,
  Minus,

  Odometer,
  OfficeBuilding,
  Open,
  Operation,
  Paperclip,
  Picture,
  Search,
  Star,
  Suitcase,
  User,
  Warning,
  Watch,
} from '@element-plus/icons-vue';
import { FileSpreadsheet, GripHorizontal, Heading1, LayoutGrid, Link2, ListOrdered, PenLine, QrCode, Sparkles, Table, Table2 } from '@vben/icons';
import {
  ElIcon,
  ElInput,
  ElMessageBox,
  ElScrollbar,
  ElTree,
} from 'element-plus';
import { storeToRefs } from 'pinia';
import draggable from 'vuedraggable';

import { useFormDesignStore } from '../store/formDesignStore';
import FieldPanel from './FieldPanel.vue';

const store = useFormDesignStore();
const { formConf, templates } = storeToRefs(store);
// 直接使用 store 中的 cloneComponent 方法
const cloneComponent = store.cloneComponent;

const getTemplateIcon = (iconName: any | string) => {
  if (typeof iconName !== 'string') return iconName;
  const map: any = { User, Edit, Document };
  return map[iconName] || Document;
};

const onDragStart = () => store.setDragging(true);
const onDragEnd = () => store.setDragging(false);

// 点击添加组件到画布
const handleClickAdd = (component: any) => {
  store.addComponent(component);
};

const activeTab = ref('field');
const activeGroups = ref(['basic', 'advanced', 'layout']);
const searchKeyword = ref('');

// 左侧导航配置
const navTabs = [
  { name: 'field', label: $t('form-design.field'), icon: Connection },
  { name: 'library', label: $t('form-design.library'), icon: Grid },
  { name: 'outline', label: $t('form-design.outline'), icon: List },
  { name: 'template', label: $t('form-design.templateLabel'), icon: Files },
];

const getAllComponents = () => [
  ...basicComponents,
  ...advancedComponents,
  ...layoutComponents,
];

const transformToTree = (items: any[]) => {
  return items.map((item) => {
    const compDef = getAllComponents().find((c) => c.type === item.type);
    const node: any = {
      id: item.id,
      label: item.label || (compDef ? compDef.label : item.type),
      icon: compDef ? compDef.icon : null,
      children: [],
    };

    if (item.columns) {
      item.columns.forEach((col: any, index: number) => {
        node.children.push({
          id: `${item.id}_col_${index}`,
          label: `${$t('form-design.attribute.layout.column')} ${index + 1}`,
          children: transformToTree(col.children || []),
          isVirtual: true,
          parentId: item.id,
        });
      });
    } else if (item.items) {
      // Collapse / Tabs
      item.items.forEach((subItem: any, index: number) => {
        node.children.push({
          id: `${item.id}_item_${index}`,
          label:
            subItem.title ||
            subItem.label ||
            subItem.name ||
            `${$t('form-design.attribute.layout.addPanel')} ${index + 1}`,
          children: transformToTree(subItem.children || []),
          isVirtual: true,
          parentId: item.id,
        });
      });
    } else if (item.children) {
      // SubTable
      node.children = transformToTree(item.children);
    }

    return node;
  });
};

const outlineData = computed(() => transformToTree(formConf.value.items));

const treeRef = ref<InstanceType<typeof ElTree>>();

watch(searchKeyword, (val) => {
  if (activeTab.value === 'outline') {
    treeRef.value?.filter(val);
  }
});

// 切换 Tab 时清空搜索框
watch(activeTab, () => {
  searchKeyword.value = '';
});

const filterNode = (value: string, data: any) => {
  if (!value) return true;
  return data.label.toLowerCase().includes(value.toLowerCase());
};

const filterComponents = (list: any[]) => {
  if (!searchKeyword.value) return list;
  const keyword = searchKeyword.value.toLowerCase();
  return list.filter(
    (item) =>
      item.label.toLowerCase().includes(keyword) ||
      item.type.toLowerCase().includes(keyword),
  );
};

const filteredBasicComponents = computed(() =>
  filterComponents(basicComponents),
);
const filteredAdvancedComponents = computed(() =>
  filterComponents(advancedComponents),
);
const filteredLayoutComponents = computed(() =>
  filterComponents(layoutComponents),
);

const filteredTemplates = computed(() => {
  if (!searchKeyword.value) return templates.value;
  const keyword = searchKeyword.value.toLowerCase();
  return templates.value.filter((tpl) =>
    tpl.title.toLowerCase().includes(keyword),
  );
});

const handleNodeClick = (data: any) => {
  if (data.isVirtual && data.parentId) {
    store.setActive(data.parentId);
  } else if (!data.isVirtual) {
    store.setActive(data.id);
  }
};

const toggleGroup = (group: string) => {
  const index = activeGroups.value.indexOf(group);
  if (index === -1) {
    activeGroups.value.push(group);
  } else {
    activeGroups.value.splice(index, 1);
  }
};

const applyTemplate = (tpl: any) => {
  ElMessageBox.confirm($t('form-design.template.applyConfirm'), $t('common.tips'), {
    type: 'warning',
    confirmButtonText: $t('common.ok'),
    cancelButtonText: $t('common.cancel'),
  }).then(() => {
    // 使用 cloneComponent 为模板项生成新的 ID
    const newItems = tpl.items.map((item: any) => store.cloneComponent(item));
    formConf.value.items = newItems;
    store.setActive(null);
  });
};

const basicComponents = [
  {
    type: 'input',
    label: $t('form-design.material.components.input'),
    icon: markRaw(Edit),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      clearable: true,
      width: '100%',
      readonly: false,
      disabled: false,
      maxlength: null,
      showWordLimit: true,
      showPassword: false,
    },
  },
  {
    type: 'textarea',
    label: $t('form-design.material.components.textarea'),
    icon: markRaw(Document),
    props: {
      type: 'textarea',
      placeholder: $t('form-design.attribute.placeholder'),
      rows: 3,
      width: '100%',
      readonly: false,
      disabled: false,
      maxlength: null,
      showWordLimit: true,
    },
  },
  {
    type: 'rich-text',
    label: $t('form-design.material.components.richText'),
    icon: markRaw(Edit),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      minHeight: 200,
      maxHeight: 500,
      width: '100%',
      disabled: false,
      toolbarConfig: {
        insert: {
          link: true,
          image: true,
          table: true,
          attachment: false,
          video: false,
        },
      },
    },
  },
  {
    type: 'select',
    label: $t('form-design.material.components.select'),
    icon: markRaw(List),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      clearable: true,
      width: '100%',
      disabled: false,
      filterable: false,
      multiple: false,
      collapseTags: false,
    },
    options: [
      { label: `${$t('form-design.attribute.addOption')} 1`, value: 1 },
      { label: `${$t('form-design.attribute.addOption')} 2`, value: 2 },
    ],
  },
  {
    type: 'cascader',
    label: $t('form-design.material.components.cascader'),
    icon: markRaw(Connection),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      clearable: true,
      disabled: false,
      separator: '/',
      filterable: false,
      emitPath: false,
      checkStrictly: false,
      width: '100%',
    },
    options: [
      {
        label: `${$t('form-design.attribute.addOption')} 1`,
        value: 1,
        children: [
          { label: `${$t('form-design.attribute.addChild')} 1`, value: 11, children: [] },
          { label: `${$t('form-design.attribute.addChild')} 2`, value: 12, children: [] },
        ],
      },
      { label: `${$t('form-design.attribute.addOption')} 2`, value: 2, children: [] },
    ],
  },
  {
    type: 'tree-select',
    label: $t('form-design.material.components.treeSelect'),
    icon: markRaw(Folder),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      clearable: true,
      disabled: false,
      multiple: false,
      showCheckbox: false,
      checkStrictly: false,
      filterable: false,
      checkOnClickNode: true,
      width: '100%',
    },
    options: [
      {
        label: `${$t('form-design.attribute.addOption')} 1`,
        value: 1,
        children: [
          { label: `${$t('form-design.attribute.addChild')} 1`, value: 11, children: [] },
          { label: `${$t('form-design.attribute.addChild')} 2`, value: 12, children: [] },
        ],
      },
      { label: `${$t('form-design.attribute.addOption')} 2`, value: 2, children: [] },
    ],
  },
  {
    type: 'radio',
    label: $t('form-design.material.components.radio'),
    icon: markRaw(CircleCheck),
    props: {
      disabled: false,
      border: false,
    },
    options: [
      { label: `${$t('form-design.attribute.addOption')} 1`, value: 1 },
      { label: `${$t('form-design.attribute.addOption')} 2`, value: 2 },
    ],
  },
  {
    type: 'checkbox',
    label: $t('form-design.material.components.checkbox'),
    icon: markRaw(Check),
    props: {
      disabled: false,
      border: false,
    },
    options: [
      { label: `${$t('form-design.attribute.addOption')} 1`, value: 1 },
      { label: `${$t('form-design.attribute.addOption')} 2`, value: 2 },
    ],
  },
  {
    type: 'date',
    label: $t('form-design.material.components.date'),
    icon: markRaw(Calendar),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      type: 'date',
      format: 'YYYY-MM-DD',
      valueFormat: 'YYYY-MM-DD',
      width: '100%',
      disabled: false,
      rangeSeparator: '-',
      startPlaceholder: $t('form-design.attribute.layout.startPlaceholder'),
      endPlaceholder: $t('form-design.attribute.layout.endPlaceholder'),
      editable: true,
    },
  },
  {
    type: 'input-number',
    label: $t('form-design.material.components.number'),
    icon: markRaw(Odometer),
    props: {
      min: 0,
      max: 100,
      step: 1,
      width: '100%',
      disabled: false,
      precision: 0,
      controls: true,
      controlsPosition: '', // default or right
    },
  },
  {
    type: 'time',
    label: $t('form-design.material.components.time'),
    icon: markRaw(Clock),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      format: 'HH:mm:ss',
      valueFormat: 'HH:mm:ss',
      width: '100%',
      disabled: false,
      arrowControl: false,
    },
  },
  {
    type: 'switch',
    label: $t('form-design.material.components.switch'),
    icon: markRaw(Open),
    props: {
      activeText: '',
      inactiveText: '',
      disabled: false,
      width: 40,
      inlinePrompt: false,
    },
  },
  {
    type: 'slider',
    label: $t('form-design.material.components.slider'),
    icon: markRaw(Operation),
    props: {
      min: 0,
      max: 100,
      step: 1,
      width: '100%',
      disabled: false,
      range: false,
      showStops: false,
      showInput: false,
    },
  },
  {
    type: 'alert',
    label: $t('form-design.material.components.alert'),
    icon: markRaw(Warning),
    props: {
      title: $t('form-design.attribute.nodeLabel'),
      type: 'info',
      description: '',
      showIcon: true,
      closable: false,
      center: false,
    },
  },
  // 移动端不支持，已注释
  // {
  //   type: 'timeline',
  //   label: $t('form-design.material.components.timeline'),
  //   icon: markRaw(More),
  //   props: {
  //     reverse: false,
  //   },
  //   items: [
  //     { timestamp: '2024-01-01', content: `${$t('form-design.attribute.layout.addPanel')} 1`, type: 'primary', icon: '' },
  //     { timestamp: '2024-01-02', content: `${$t('form-design.attribute.layout.addPanel')} 2`, type: 'success', icon: '' },
  //     { timestamp: '2024-01-03', content: `${$t('form-design.attribute.layout.addPanel')} 3`, type: 'warning', icon: '' },
  //   ],
  // },
  {
    type: 'rate',
    label: $t('form-design.material.components.rate'),
    icon: markRaw(Star),
    props: {
      max: 5,
      disabled: false,
      allowHalf: false,
      showScore: false,
    },
  },
  {
    type: 'color',
    label: $t('form-design.material.components.color'),
    icon: markRaw(MagicStick),
    props: {
      disabled: false,
      showAlpha: false,
    },
  },
];

const advancedComponents: any[] = [
  {
    type: 'dept-selector',
    label: $t('form-design.material.components.dept'),
    icon: markRaw(OfficeBuilding),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      clearable: true,
      disabled: false,
      filterable: true,
    },
  },
  {
    type: 'user-selector',
    label: $t('form-design.material.components.user'),
    icon: markRaw(User),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      clearable: true,
      disabled: false,
      filterable: true,
      displayMode: 'select',
    },
  },
  {
    type: 'role-selector',
    label: $t('form-design.material.components.role'),
    icon: markRaw(Avatar),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      clearable: true,
      disabled: false,
      filterable: true,
    },
  },
  {
    type: 'post-selector',
    label: $t('form-design.material.components.post'),
    icon: markRaw(Suitcase),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      clearable: true,
      disabled: false,
      filterable: true,
    },
  },
  {
    type: 'cron-selector',
    label: $t('form-design.material.components.cron'),
    icon: markRaw(Watch),
    props: {
      placeholder: $t('form-design.material.components.cron'),
      disabled: false,
      hideSecond: true,
      hideYear: true,
    },
  },
  {
    type: 'image-selector',
    label: $t('form-design.material.components.image'),
    icon: markRaw(Picture),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      disabled: false,
      clearable: true,
      maxSize: 10,
      gridColumns: 4,
      enableCrop: false,
    },
  },
  {
    type: 'file-selector',
    label: $t('form-design.material.components.file'),
    icon: markRaw(Paperclip),
    props: {
      placeholder: $t('form-design.attribute.placeholder'),
      multiple: false,
      disabled: false,
      clearable: true,
      maxSize: 100,
      showIcon: true,
      showSize: true,
      displayMode: 'popover',
    },
  },
  {
    type: 'sub-table',
    label: $t('form-design.material.components.subTable'),
    icon: markRaw(Table),
    children: [],
    props: {
      stripe: true,
      showIndex: true,
      summary: false,
      addable: true,
      deletable: true,
      showSortButtons: false,
    },
  },
  {
    type: 'current-user',
    label: $t('form-design.material.components.currentUser'),
    icon: markRaw(User),
    props: {
      displayField: 'nickname',
      valueField: 'realName',
      showAvatar: false,
      disabled: true,
      placeholder: $t('form-design.material.components.currentUser'),
      fillMode: 'onCreate',
    },
  },
  // 移动端不支持，已注释
  // {
  //   type: 'current-datetime',
  //   label: $t('form-design.material.components.currentDatetime'),
  //   icon: markRaw(Clock),
  //   props: {
  //     type: 'datetime',
  //     format: 'YYYY-MM-DD HH:mm:ss',
  //     valueFormat: 'YYYY-MM-DD HH:mm:ss',
  //     disabled: true,
  //     placeholder: $t('form-design.material.components.currentDatetime'),
  //     autoUpdate: false,
  //     fillMode: 'onCreate',
  //   },
  // },
  {
    type: 'code-generator',
    label: $t('form-design.material.components.codeGenerator'),
    icon: markRaw(QrCode),
    props: {
      prefix: '',
      separator: '-',
      generateMode: 'date_seq',
      dateFormat: 'YYYYMMDD',
      seqLength: 4,
      seqResetRule: 'daily',
      randomLength: 6,
      businessType: 'default',
      disabled: true,
      readonly: true,
      placeholder: $t('form-design.material.components.codeGenerator'),
      generateOnMount: true,
    },
  },
  // 移动端不支持，已注释
  // {
  //   type: 'money-input',
  //   label: $t('form-design.material.components.moneyInput'),
  //   icon: markRaw(Odometer),
  //   props: {
  //     precision: 2,
  //     currencySymbol: '¥',
  //     showCurrency: true,
  //     showThousandSeparator: true,
  //     showCapital: false,
  //     disabled: false,
  //     readonly: false,
  //     placeholder: $t('form-design.material.components.moneyInput'),
  //   },
  // },
  {
    type: 'formula-input',
    label: $t('form-design.material.components.formulaInput'),
    icon: markRaw(Operation),
    props: {
      width: '100%',
      formula: '',
      precision: 2,
      disabled: true,
      placeholder: $t('form-design.material.components.formulaInput'),
      showFormula: true,
    },
  },
  {
    type: 'linked-field',
    label: $t('form-design.material.components.linkedField'),
    icon: markRaw(Link2),
    props: {
      width: '100%',
      sourceField: '',
      displayField: '',
      placeholder: $t('form-design.attribute.linkedFieldPlaceholder'),
      disabled: true,
    },
  },
  {
    type: 'region-selector',
    label: $t('form-design.material.components.regionSelector'),
    icon: markRaw(Location),
    props: {
      level: 3,
      placeholder: $t('form-design.regionSelector.selectDistrict'),
      clearable: true,
      showAllLevels: true,
      separator: '/',
      dataSource: 'api',
      lazy: true,
      checkStrictly: false,
      expandTrigger: 'click',
    },
  },
  // {
  //   type: 'ai-image-ocr',
  //   label: $t('form-design.material.components.aiImageOcr'),
  //   icon: markRaw(Sparkles),
  //   props: {
  //     placeholder: $t('form-design.attribute.placeholder'),
  //     multiple: false,
  //     disabled: false,
  //     clearable: true,
  //     maxSize: 10,
  //   },
  //   aiOcrConfig: {
  //     enabled: true,
  //     templateType: 'custom',
  //     acceptFileTypes: ['image'],
  //     outputSchema: [],
  //     fieldMapping: [],
  //     confirmMode: 'manual',
  //   },
  // },
  {
    type: 'table-selector',
    label: $t('form-design.material.components.tableSelector'),
    icon: markRaw(Table2),
    props: {
      placeholder: $t('form-design.attribute.clickToSelect'),
      multiple: false,
      disabled: false,
      clearable: true,
    },
    options: [],
    dataSource: {
      type: 'static',
      formCode: '',
      formLabelField: '',
      formValueField: '',
    },
    tableSelectorConfig: {
      dialogTitle: $t('form-design.attribute.selectData'),
      dialogWidth: '800px',
      columns: [],
    },
  },
  {
    type: 'form-selector',
    label: $t('form-design.material.components.formSelector'),
    icon: markRaw(FileSpreadsheet),
    props: {
      placeholder: $t('form-design.attribute.clickToSelect'),
      multiple: false,
      disabled: false,
      clearable: true,
      dialogTitle: $t('form-design.attribute.selectData'),
      dialogWidth: '90%',
    },
    formSelectorConfig: {
      formCode: '',
      valueField: 'id',
      labelField: 'name',
    },
  },
  {
    type: 'signature-pad',
    label: $t('form-design.material.components.signaturePad'),
    icon: markRaw(PenLine),
    props: {
      placeholder: $t('form-design.signaturePad.placeholder'),
      penColor: '#000000',
      penWidth: 2,
      backgroundColor: 'transparent',
      height: 200,
      disabled: false,
    },
  },
  {
    type: 'qrcode-generator',
    label: $t('form-design.material.components.qrcodeGenerator'),
    icon: markRaw(QrCode),
    props: {
      placeholder: $t('form-design.qrcode.placeholder'),
      dataSource: 'static',
      qrcodeType: 'text',
      size: 200,
      errorCorrectionLevel: 'M',
      foregroundColor: '#000000',
      backgroundColor: '#FFFFFF',
      margin: 2,
      showContent: false,
      enableDownload: false,
      enableCopy: false,
      disabled: false,
    },
  },
];

const layoutComponents = [
  {
    type: 'grid',
    label: $t('form-design.material.components.grid'),
    icon: markRaw(LayoutGrid),
    columns: [
      { span: 12, children: [] },
      { span: 12, children: [] },
    ],
    props: {
      gutter: 12,
      justify: 'start',
      align: 'top',
    },
  },
  {
    type: 'divider',
    label: $t('form-design.material.components.divider'),
    icon: markRaw(Minus),
    props: {
      contentPosition: 'center',
      borderStyle: 'solid',
      direction: 'horizontal',
    },
  },
  {
    type: 'collapse',
    label: $t('form-design.material.components.collapse'),
    icon: markRaw(CaretBottom),
    props: {
      accordion: false,
    },
    items: [
      { title: `${$t('form-design.attribute.layout.addPanel')} 1`, name: '1', children: [] },
      { title: `${$t('form-design.attribute.layout.addPanel')} 2`, name: '2', children: [] },
    ],
  },
  {
    type: 'tabs',
    label: $t('form-design.material.components.tabs'),
    icon: markRaw(Files),
    props: {
      type: '', // card, border-card
      tabPosition: 'top',
    },
    items: [
      { label: `${$t('form-design.attribute.layout.addTab')} 1`, name: '1', children: [] },
      { label: `${$t('form-design.attribute.layout.addTab')} 2`, name: '2', children: [] },
    ],
  },
  {
    type: 'title',
    label: $t('form-design.material.components.title'),
    icon: markRaw(Heading1),
    props: {
      text: $t('form-design.material.components.title'),
      fontSize: 15,
      showBar: true,
      theme: 'primary',
      showBorder: false,
    },
  },
  {
    type: 'spacer',
    label: $t('form-design.material.components.spacer'),
    icon: markRaw(GripHorizontal),
    props: {
      height: 24,
    },
  },
  {
    type: 'steps',
    label: $t('form-design.material.components.steps'),
    icon: markRaw(ListOrdered),
    props: {
      direction: 'horizontal',
      alignCenter: false,
      simple: false,
      finishStatus: 'success',
      processStatus: 'process',
    },
    items: [
      { title: `${$t('form-design.attribute.layout.addStep')} 1`, description: '', name: '1', children: [] },
      { title: `${$t('form-design.attribute.layout.addStep')} 2`, description: '', name: '2', children: [] },
      { title: `${$t('form-design.attribute.layout.addStep')} 3`, description: '', name: '3', children: [] },
    ],
  },
];
</script>

<template>
  <div
    class="material-panel flex h-full rounded border-[var(--el-border-color)] bg-[var(--el-bg-color)]"
  >
    <!-- 左侧竖向导航 -->
    <div
      class="bg-background-deep flex w-12 flex-shrink-0 flex-col border-[var(--el-border-color)] py-2"
    >
      <div
        v-for="tab in navTabs"
        :key="tab.name"
        class="nav-item group relative mx-1.5 mb-1 flex cursor-pointer flex-col items-center justify-center rounded py-2 transition-all"
        :class="
          activeTab === tab.name
            ? 'bg-[var(--el-color-primary)] text-white'
            : 'text-[var(--el-text-color-secondary)] hover:bg-[var(--el-fill-color)] hover:text-[var(--el-color-primary)]'
        "
        :title="tab.label"
        @click="activeTab = tab.name"
      >
        <ElIcon :size="18">
          <component :is="tab.icon" />
        </ElIcon>
        <span class="mt-0.5 text-[10px] leading-tight">{{ tab.label }}</span>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- 搜索框 -->
      <div class="flex-shrink-0 p-3">
        <ElInput
          v-model="searchKeyword"
          :placeholder="$t('form-design.search')"
          size="small"
          clearable
          :prefix-icon="Search"
        />
      </div>

      <!-- 数据字段面板 -->
      <div v-show="activeTab === 'field'" class="flex-1 overflow-hidden">
        <FieldPanel :search-keyword="searchKeyword" />
      </div>

      <!-- 组件库面板 -->
      <div v-show="activeTab === 'library'" class="flex-1 overflow-hidden">
        <ElScrollbar class="h-full">
          <div class="px-4 pb-4">
            <div class="component-group mb-4">
              <div
                class="group-title mb-2 flex cursor-pointer select-none items-center justify-between text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleGroup('basic')"
              >
                <span class="font-bold">{{ $t('form-design.material.basic') }}</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeGroups.includes('basic')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeGroups.includes('basic')">
                <draggable
                  v-model="filteredBasicComponents"
                  :group="{ name: 'form-design', pull: 'clone', put: false }"
                  :sort="false"
                  :clone="cloneComponent"
                  item-key="type"
                  class="grid grid-cols-2 gap-2"
                  @start="onDragStart"
                  @end="onDragEnd"
                >
                  <template #item="{ element }">
                    <div
                      class="component-item flex cursor-move flex-col items-center justify-center rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] p-2 transition-colors hover:border-[var(--el-color-primary)] hover:text-[var(--el-color-primary)]"
                      @click.stop="handleClickAdd(element)"
                    >
                      <ElIcon class="mb-1 text-lg" :size="18">
                        <component :is="element.icon" />
                      </ElIcon>
                      <span class="text-xs">{{ element.label }}</span>
                    </div>
                  </template>
                </draggable>
              </div>
            </div>

            <div class="component-group mb-4">
              <div
                class="group-title mb-2 flex cursor-pointer select-none items-center justify-between text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleGroup('advanced')"
              >
                <span class="font-bold">{{ $t('form-design.material.advanced') }}</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeGroups.includes('advanced')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeGroups.includes('advanced')">
                <div
                  v-if="filteredAdvancedComponents.length === 0"
                  class="rounded bg-[var(--el-fill-color-light)] py-2 text-center text-xs text-[var(--el-text-color-placeholder)]"
                >
                  {{ $t('form-design.material.noComponents') }}
                </div>
                <draggable
                  v-else
                  v-model="filteredAdvancedComponents"
                  :group="{ name: 'form-design', pull: 'clone', put: false }"
                  :sort="false"
                  :clone="cloneComponent"
                  item-key="type"
                  class="grid grid-cols-2 gap-2"
                  @start="onDragStart"
                  @end="onDragEnd"
                >
                  <template #item="{ element }">
                    <div
                      class="component-item flex cursor-move flex-col items-center justify-center rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] p-2 transition-colors hover:border-[var(--el-color-primary)] hover:text-[var(--el-color-primary)]"
                      @click.stop="handleClickAdd(element)"
                    >
                      <ElIcon class="mb-1 text-lg" :size="18">
                        <component :is="element.icon" />
                      </ElIcon>
                      <span class="text-xs">{{ element.label }}</span>
                    </div>
                  </template>
                </draggable>
              </div>
            </div>

            <div class="component-group">
              <div
                class="group-title mb-2 flex cursor-pointer select-none items-center justify-between text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleGroup('layout')"
              >
                <span class="font-bold">{{ $t('form-design.material.layout') }}</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeGroups.includes('layout')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeGroups.includes('layout')">
                <draggable
                  v-model="filteredLayoutComponents"
                  :group="{ name: 'form-design', pull: 'clone', put: false }"
                  :sort="false"
                  :clone="cloneComponent"
                  item-key="type"
                  class="grid grid-cols-2 gap-2"
                  @start="onDragStart"
                  @end="onDragEnd"
                >
                  <template #item="{ element }">
                    <div
                      class="component-item flex cursor-move flex-col items-center justify-center rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] p-2 transition-colors hover:border-[var(--el-color-primary)] hover:text-[var(--el-color-primary)]"
                      @click.stop="handleClickAdd(element)"
                    >
                      <ElIcon class="mb-1 text-lg" :size="18">
                        <component :is="element.icon" />
                      </ElIcon>
                      <span class="text-xs">{{ element.label }}</span>
                    </div>
                  </template>
                </draggable>
              </div>
            </div>
          </div>
        </ElScrollbar>
      </div>

      <!-- 大纲面板 -->
      <div v-show="activeTab === 'outline'" class="flex-1 overflow-hidden">
        <ElScrollbar class="h-full">
          <div>
            <ElTree
              ref="treeRef"
              :data="outlineData"
              node-key="id"
              default-expand-all
              highlight-current
              :expand-on-click-node="false"
              :filter-node-method="filterNode"
              @node-click="handleNodeClick"
            >
              <template #default="{ node, data }">
                <div class="flex items-center text-xs">
                  <ElIcon class="mr-1" v-if="data.icon">
                    <component :is="data.icon" />
                  </ElIcon>
                  <span
                    :class="{
                      'text-[var(--el-text-color-placeholder)]': data.isVirtual,
                    }"
                    >{{ node.label }}</span
                  >
                </div>
              </template>
            </ElTree>
          </div>
        </ElScrollbar>
      </div>

      <!-- 模板面板 -->
      <div v-show="activeTab === 'template'" class="flex-1 overflow-hidden">
        <ElScrollbar class="h-full">
          <div class="grid grid-cols-2 gap-4 p-4">
            <div
              v-for="(tpl, index) in filteredTemplates"
              :key="index"
              class="flex cursor-pointer flex-col items-center justify-center rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] p-4 transition-all hover:border-[var(--el-color-primary)] hover:shadow-sm"
              @click="applyTemplate(tpl)"
            >
              <ElIcon
                :size="24"
                class="mb-2 text-[var(--el-text-color-secondary)]"
              >
                <component :is="getTemplateIcon(tpl.icon)" />
              </ElIcon>
              <span class="text-xs text-[var(--el-text-color-regular)]">{{
                tpl.title
              }}</span>
            </div>
          </div>
        </ElScrollbar>
      </div>
    </div>
  </div>
</template>

<style scoped>
.nav-item {
  min-height: 48px;
}
</style>
