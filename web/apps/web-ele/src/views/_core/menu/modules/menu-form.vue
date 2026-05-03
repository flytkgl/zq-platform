<script lang="ts" setup>
import type { Recordable } from '@vben/types';

import type { VbenFormSchema } from '#/adapter/form';
import type { Menu } from '#/api/core/menu';

import { computed, h, ref, watch } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t, $te } from '@vben/locales';
import { getPopupContainer } from '@vben/utils';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElMessage,
  ElScrollbar,
} from 'element-plus';

import { useVbenForm, z } from '#/adapter/form';
import { getApplicationListApi } from '#/api/core/application';
import {
  checkMenuNameApi,
  checkMenuPathApi,
  getAllMenuTreeApi,
  updateMenuApi,
} from '#/api/core/menu';
import { getPageListApi } from '#/api/online-dev/page-manager';
import { componentKeys } from '#/router/routes';
import { useAppContextStore } from '#/store/app-context';

import { getMenuTypeOptions } from '../data';

const props = defineProps<{
  menu?: Menu;
}>();

const emit = defineEmits<{
  success: [];
}>();

const appContextStore = useAppContextStore();

/**
 * 处理菜单数据，添加 name 字段用于显示国际化文本
 */
function processMenuData(menus: any[]): any[] {
  return menus.map((menu) => ({
    ...menu,
    name: menu.title ? $t(menu.title) : menu.name,
    children: menu.children ? processMenuData(menu.children) : undefined,
  }));
}

/**
 * 包装 API 调用，处理返回的数据
 */
async function getMenuListProcessed() {
  const applicationId = appContextStore.currentApp?.id;
  const data = await getAllMenuTreeApi(applicationId);
  return processMenuData(data);
}

/**
 * 检查菜单名称是否存在
 */
async function isMenuNameExists(name: string, excludeId?: string) {
  const applicationId = appContextStore.currentApp?.id;
  const result = await checkMenuNameApi(name, excludeId, applicationId);
  return result.exists;
}

/**
 * 检查菜单路径是否存在
 */
async function isMenuPathExists(path: string, excludeId?: string) {
  const applicationId = appContextStore.currentApp?.id;
  const result = await checkMenuPathApi(path, excludeId, applicationId);
  return result.exists;
}

// Badge variants options
const BadgeVariants = [
  'default',
  'destructive',
  'success',
  'warning',
  'primary',
  'outline',
];

function getFormSchema(
  getCurrentMenuId: () => string | undefined,
): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'id',
      hide: true,
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: getMenuTypeOptions(),
        isButton: true,
      },
      defaultValue: 'menu',
      fieldName: 'type',
      formItemClass: 'col-span-2 md:col-span-2',
      label: $t('menu.type'),
    },
    {
      component: 'Input',
      componentProps: {
        clearable: true,
      },
      fieldName: 'name',
      label: $t('menu.menuName'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('menu.menuName'), 2]))
        .max(30, $t('ui.formRules.maxLength', [$t('menu.menuName'), 30]))
        .superRefine(async (value, ctx) => {
          // 获取当前菜单的 ID，用于排除自身
          const currentId = getCurrentMenuId();
          const exists = await isMenuNameExists(value, currentId);
          if (exists) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: $t('ui.formRules.alreadyExists', [
                $t('menu.menuName'),
                value,
              ]),
            });
          }
        }),
    },
    {
      component: 'ApiTreeSelect',
      componentProps: {
        api: getMenuListProcessed,
        checkStrictly: true,
        clearable: true,
        class: 'w-full',
        filterTreeNode(input: string, node: Recordable<any>) {
          if (!input || input.length === 0) {
            return true;
          }
          const name: string = node.name ?? '';
          return name.toLowerCase().includes(input.toLowerCase());
        },
        getPopupContainer,
        labelField: 'name',
        showSearch: true,
        treeDefaultExpandAll: true,
        valueField: 'id',
        childrenField: 'children',
      },
      fieldName: 'parent_id',
      label: $t('menu.parent'),
      renderComponentContent() {
        return {
          title({ label, icon }: { icon?: string; label: string }) {
            const coms = [];
            if (!label) return '';
            if (icon) {
              coms.push(h(IconifyIcon, { class: 'size-4', icon }));
            }
            coms.push(h('span', { class: '' }, label));
            return h('div', { class: 'flex items-center gap-1' }, coms);
          },
        };
      },
    },
    {
      component: 'Input',
      componentProps() {
        return {
          clearable: true,
          onInput(value: string) {
            // 当输入变化时，检查翻译是否存在并更新后缀
            titleSuffix.value = value && $te(value) ? $t(value) : undefined;
          },
        };
      },
      fieldName: 'title',
      label: $t('menu.menuTitle'),
      rules: 'required',
      renderComponentContent() {
        return {
          // 使用 append 插槽显示翻译后的值
          append: () => titleSuffix.value || '',
        };
      },
    },
    {
      component: 'Input',
      componentProps: {
        clearable: true,
      },
      dependencies: {
        show: (values) => {
          return [
            'agent',
            'catalog',
            'embedded',
            'menu',
            'online_form',
            'online_page',
          ].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'path',
      label: $t('menu.path'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('menu.path'), 2]))
        .max(100, $t('ui.formRules.maxLength', [$t('menu.path'), 100]))
        .refine(
          (value: string) => {
            return value.startsWith('/');
          },
          $t('ui.formRules.startWith', [$t('menu.path'), '/']),
        )
        .superRefine(async (value, ctx) => {
          // 获取当前菜单的 ID，用于排除自身
          const currentId = getCurrentMenuId();
          const exists = await isMenuPathExists(value, currentId);
          if (exists) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: $t('ui.formRules.alreadyExists', [
                $t('menu.path'),
                value,
              ]),
            });
          }
        }),
    },
    {
      component: 'Input',
      componentProps: {
        clearable: true,
      },
      dependencies: {
        show: (values) => {
          return ['embedded', 'menu'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'activePath',
      help: $t('menu.activePathHelp'),
      label: $t('menu.activePath'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('menu.path'), 2]))
        .max(100, $t('ui.formRules.maxLength', [$t('menu.path'), 100]))
        .refine(
          (value: string) => {
            return value.startsWith('/');
          },
          $t('ui.formRules.startWith', [$t('menu.path'), '/']),
        )
        .superRefine(async (value, ctx) => {
          // 获取当前菜单的 ID，用于排除自身
          const currentId = getCurrentMenuId();
          const exists = await isMenuPathExists(value, currentId);
          if (!exists) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: $t('menu.activePathMustExist'),
            });
          }
        })
        .optional(),
    },
    {
      component: 'IconPicker',
      componentProps: {
        prefix: 'lucide',
        clearable: true,
      },
      dependencies: {
        show: (values) => {
          return [
            'catalog',
            'embedded',
            'link',
            'menu',
            'online_form',
            'online_page',
          ].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'icon',
      label: $t('menu.icon'),
    },
    {
      component: 'IconPicker',
      componentProps: {
        prefix: 'carbon',
        clearable: true,
      },
      dependencies: {
        show: (values) => {
          return [
            'agent',
            'catalog',
            'embedded',
            'menu',
            'online_form',
            'online_page',
          ].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'activeIcon',
      label: $t('menu.activeIcon'),
    },
    {
      component: 'Select',
      componentProps: {
        clearable: true,
        class: 'w-full',
        options: componentKeys.map((v) => ({ label: v, value: v })),
        filterable: true,
        'filter-placeholder': $t('ui.placeholder.select'),
      },
      dependencies: {
        rules: (values) => {
          return values.type === 'menu' ? 'required' : null;
        },
        show: (values) => {
          return values.type === 'menu';
        },
        triggerFields: ['type'],
      },
      fieldName: 'component',
      label: $t('menu.component'),
    },
    {
      component: 'Input',
      fieldName: 'formCode',
      hide: true,
    },
    {
      component: 'ApiSelect',
      componentProps: {
        api: async () => {
          const res = await getPageListApi({
            status: 'published',
            pageSize: 100,
          });
          return res.items.map((item) => ({
            label: `${item.name} (${item.code})`,
            value: item.code,
          }));
        },
        class: 'w-full',
        filterable: true,
        placeholder: $t('ui.placeholder.select'),
      },
      dependencies: {
        rules: (values) => {
          return values.type === 'online_page' ? 'required' : null;
        },
        show: (values) => {
          return values.type === 'online_page';
        },
        triggerFields: ['type'],
      },
      fieldName: 'pageCode',
      label: $t('menu.pageCode'),
    },
    {
      component: 'ApiSelect',
      componentProps: {
        api: async () => {
          const res = await getApplicationListApi({
            pageSize: 100,
          });
          return res.items.map((item) => ({
            label: `${item.name} (${item.code})`,
            value: item.id,
          }));
        },
        clearable: true,
        class: 'w-full',
        filterable: true,
        placeholder: $t('menu.applicationIdHelp'),
      },
      defaultValue: appContextStore.currentApp?.id,
      fieldName: 'application_id',
      help: $t('menu.applicationIdHelp'),
      label: $t('menu.applicationId'),
    },
    {
      component: 'Input',
      componentProps: {
        clearable: true,
      },
      dependencies: {
        show: (values) => {
          return ['embedded', 'link'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'linkSrc',
      label: $t('menu.linkSrc'),
      rules: z.string().url($t('ui.formRules.invalidURL')),
    },
    // {
    //   component: 'Input',
    //   componentProps: {
    //     clearable: true,
    //   },
    //   dependencies: {
    //     rules: (values) => {
    //       return values.type === 'button' ? 'required' : null;
    //     },
    //     show: (values) => {
    //       return [
    //         'catalog',
    //         'embedded',
    //         'menu',
    //         'online_form',
    //         'online_page',
    //       ].includes(values.type);
    //     },
    //     triggerFields: ['type'],
    //   },
    //   fieldName: 'authCode',
    //   label: $t('menu.authCode'),
    // },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.enabled'), value: 1 },
          { label: $t('common.disabled'), value: 0 },
        ],
        isButton: true,
      },
      defaultValue: 1,
      fieldName: 'status',
      label: $t('menu.status'),
    },
    {
      component: 'Select',
      componentProps: {
        clearable: true,
        class: 'w-full',
        options: [
          { label: $t('menu.badgeType.dot'), value: 'dot' },
          { label: $t('menu.badgeType.normal'), value: 'normal' },
        ],
      },
      dependencies: {
        show: (values) => {
          return values.type !== 'button';
        },
        triggerFields: ['type'],
      },
      fieldName: 'badgeType',
      label: $t('menu.badgeType.title'),
    },
    {
      component: 'Input',
      componentProps: (values) => {
        return {
          clearable: true,
          class: 'w-full',
          disabled: values.badgeType !== 'normal',
        };
      },
      dependencies: {
        show: (values) => {
          return values.type !== 'button';
        },
        triggerFields: ['type', 'badgeType'],
      },
      fieldName: 'badge',
      label: $t('menu.badge'),
    },
    {
      component: 'Select',
      componentProps: {
        clearable: true,
        class: 'w-full',
        options: BadgeVariants.map((v) => ({
          label: v,
          value: v,
        })),
      },
      dependencies: {
        show: (values) => {
          return values.type !== 'button';
        },
        triggerFields: ['type'],
      },
      fieldName: 'badgeVariants',
      label: $t('menu.badgeVariants'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        clearable: true,
        class: 'w-full',
      },
      fieldName: 'order',
      label: $t('menu.order'),
    },
    {
      component: 'Divider',
      dependencies: {
        show: (values) => {
          return !['link'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'divider1',
      formItemClass: 'col-span-2 md:col-span-2 pb-0',
      hideLabel: true,
      renderComponentContent() {
        return {
          default: () => $t('menu.advancedSettings'),
        };
      },
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.enabled'), value: true },
          { label: $t('common.disabled'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return ['agent', 'menu', 'online_form', 'online_page'].includes(
            values.type,
          );
        },
        triggerFields: ['type'],
      },
      fieldName: 'keepAlive',
      label: $t('menu.keepAlive'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.enabled'), value: true },
          { label: $t('common.disabled'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return [
            'agent',
            'embedded',
            'menu',
            'online_form',
            'online_page',
          ].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'affixTab',
      label: $t('menu.affixTab'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return !['button'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'hideInMenu',
      label: $t('menu.hideInMenu'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return ['catalog', 'menu'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'hideChildrenInMenu',
      label: $t('menu.hideChildrenInMenu'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return !['link'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'hideInBreadcrumb',
      label: $t('menu.hideInBreadcrumb'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return !['link'].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'hideInTab',
      label: $t('menu.hideInTab'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      dependencies: {
        show: (values) => {
          return [
            'agent',
            'embedded',
            'menu',
            'online_form',
            'online_page',
          ].includes(values.type);
        },
        triggerFields: ['type'],
      },
      fieldName: 'noBasicLayout',
      label: $t('menu.noBasicLayout'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: true,
      dependencies: {
        show: (values) => {
          return ['agent', 'menu', 'online_form', 'online_page'].includes(
            values.type,
          );
        },
        triggerFields: ['type'],
      },
      fieldName: 'fullPathKey',
      help: $t('menu.fullPathKeyHelp'),
      label: $t('menu.fullPathKey'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ],
        isButton: true,
      },
      defaultValue: false,
      fieldName: 'is_system',
      help: $t('menu.isSystemHelp'),
      label: $t('menu.isSystem'),
    },
  ];
}

const formData = ref<Menu>();
const titleSuffix = ref<string>();
const isEditMode = ref(false); // 编辑模式
const isUpdating = ref(false); // 更新中状态

// 创建一个函数来获取当前的菜单 ID，用于验证时排除自身
const getCurrentMenuId = () => formData.value?.id;

const schema = computed(() => {
  return getFormSchema(getCurrentMenuId);
});

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  commonConfig: {
    colon: true,
    // formItemClass: 'col-span-2 md:col-span-1',
    disabled: true, // 默认禁用
  },
  schema: schema.value,
  showDefaultActions: false, // 不显示默认按钮
  wrapperClass: 'grid-cols-2 gap-x-4',
});

/**
 * 进入编辑模式
 */
function onEdit() {
  isEditMode.value = true;
  formApi.setState({ commonConfig: { disabled: false } });
}

/**
 * 取消编辑
 */
function onCancel() {
  isEditMode.value = false;
  formApi.setState({ commonConfig: { disabled: true } });
  // 重新加载表单数据
  if (props.menu) {
    const menuData = { ...props.menu };
    switch (menuData.type) {
      case 'embedded': {
        (menuData as any).linkSrc = menuData.iframeSrc;

        break;
      }
      case 'link': {
        (menuData as any).linkSrc = menuData.link;

        break;
      }
      case 'online_form': {
        (menuData as any).formCode = menuData.query?.formCode;

        break;
      }
      case 'online_page': {
        (menuData as any).pageCode = menuData.query?.pageCode;

        break;
      }
      // No default
    }
    formApi.setValues(menuData);
  }
}

/**
 * 更新菜单
 */
async function onUpdate() {
  // 在验证之前就设置 loading 状态（因为验证过程中会调用 check API）
  isUpdating.value = true;

  try {
    const { valid } = await formApi.validate();
    if (valid) {
      const data = (await formApi.getValues()) as any;
      switch (data.type) {
        case 'embedded': {
          data.iframeSrc = data.linkSrc;

          break;
        }
        case 'link': {
          data.link = data.linkSrc;

          break;
        }
        case 'online_form': {
          data.query = { formCode: data.formCode };
          data.component = 'online-dev/form-render/index';

          break;
        }
        case 'online_page': {
          data.query = { pageCode: data.pageCode };
          data.component = 'online-dev/page-render/index';

          break;
        }
        // No default
      }
      delete data.linkSrc;
      delete data.formCode;
      delete data.pageCode;

      // 确保 parent_id 清空时发送 null 而不是 undefined
      if (data.parent_id === undefined || data.parent_id === '') {
        data.parent_id = null;
      }

      // 确保 application_id 清空时发送 null 而不是 undefined
      if (data.application_id === undefined || data.application_id === '') {
        data.application_id = null;
      }

      if (formData.value?.id) {
        await updateMenuApi(formData.value.id, data);
        ElMessage.success($t('ui.actionMessage.updateSuccess'));
        isEditMode.value = false; // 退出编辑模式
        formApi.setState({ commonConfig: { disabled: true } });
        // 更新成功后通知父组件刷新，但不清空当前表单
        emit('success');
      }
    }
  } catch {
    ElMessage.error($t('ui.actionMessage.updateError'));
  } finally {
    isUpdating.value = false;
  }
}

/**
 * 重置表单
 */
function onReset() {
  // 重新加载原始数据
  if (props.menu) {
    const menuData = { ...props.menu };
    switch (menuData.type) {
      case 'embedded': {
        (menuData as any).linkSrc = menuData.iframeSrc;

        break;
      }
      case 'link': {
        (menuData as any).linkSrc = menuData.link;

        break;
      }
      case 'online_form': {
        (menuData as any).formCode = menuData.query?.formCode;

        break;
      }
      case 'online_page': {
        (menuData as any).pageCode = menuData.query?.pageCode;

        break;
      }
      // No default
    }
    formApi.setValues(menuData);
  }
}

// 监听props中的menu变化
watch(
  () => props.menu,
  (newMenu) => {
    isEditMode.value = false; // 切换菜单时退出编辑模式
    if (newMenu?.id) {
      const menuData = { ...newMenu };
      switch (menuData.type) {
        case 'embedded': {
          (menuData as any).linkSrc = menuData.iframeSrc;

          break;
        }
        case 'link': {
          (menuData as any).linkSrc = menuData.link;

          break;
        }
        case 'online_form': {
          (menuData as any).formCode = menuData.query?.formCode;

          break;
        }
        case 'online_page': {
          (menuData as any).pageCode = menuData.query?.pageCode;

          break;
        }
        // No default
      }
      formData.value = menuData;
      formApi.setValues(formData.value);
      // 初始化 titleSuffix
      titleSuffix.value =
        newMenu.title && $te(newMenu.title) ? $t(newMenu.title) : undefined;
    } else {
      formApi.resetForm();
      titleSuffix.value = undefined;
    }
  },
  { immediate: true, deep: true },
);

// 监听 schema 变化，动态更新表单配置
watch(schema, (newSchema) => {
  formApi.updateSchema(newSchema);
});

// 暴露方法给父组件
defineExpose({
  enterEditMode: onEdit,
});
</script>

<template>
  <ElCard
    class="h-full"
    :class="[menu ? 'flex flex-col' : 'empty-state-card']"
    style="border: none"
    shadow="never"
    :body-style="
      !menu
        ? { height: '100%', padding: 0 }
        : {
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            overflow: 'hidden',
          }
    "
  >
    <!-- 没有选中菜单时显示空状态 -->
    <div v-if="!menu" class="flex h-full w-full items-center justify-center">
      <ElEmpty :description="$t('menu.selectMenu')" />
    </div>

    <!-- 选中菜单时显示表单 -->
    <template v-if="menu" #header>
      <div class="flex items-center justify-between">
        <span class="text-base font-medium">
          {{ formData?.title ? $t(formData.title) : $t('menu.menuDetail') }}
        </span>
        <div class="flex gap-2">
          <!-- 非编辑模式：显示编辑按钮 -->
          <ElButton
            v-if="!isEditMode && formData?.id"
            type="primary"
            size="small"
            @click="onEdit"
          >
            <IconifyIcon icon="carbon:edit" class="mr-1 size-4" />
            {{ $t('common.edit') }}
          </ElButton>

          <!-- 编辑模式：显示取消、重置和更新按钮 -->
          <template v-if="isEditMode">
            <ElButton size="small" @click="onCancel">
              <IconifyIcon icon="carbon:close" class="mr-1 size-4" />
              {{ $t('common.cancel') }}
            </ElButton>
            <ElButton size="small" :disabled="isUpdating" @click="onReset">
              <IconifyIcon icon="carbon:reset" class="mr-1 size-4" />
              {{ $t('common.reset') }}
            </ElButton>
            <ElButton
              type="primary"
              size="small"
              :loading="isUpdating"
              @click="onUpdate"
            >
              <IconifyIcon
                v-if="!isUpdating"
                icon="carbon:checkmark"
                class="mr-1 size-4"
              />
              {{ $t('common.update') }}
            </ElButton>
          </template>
        </div>
      </div>
    </template>

    <ElScrollbar v-if="menu" class="flex-1">
      <Form class="px-2" />
    </ElScrollbar>
  </ElCard>
</template>

<style scoped>
.empty-state-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}
</style>
