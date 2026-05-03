<script lang="ts" setup>
import type { Recordable } from '@vben/types';

import type { VbenFormSchema } from '#/adapter/form';
import type { Menu } from '#/api/core/menu';

import { computed, h, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t, $te } from '@vben/locales';
import { getPopupContainer } from '@vben/utils';

import { ElMessage } from 'element-plus';

import { useVbenForm, z } from '#/adapter/form';
import {
  checkMenuNameApi,
  checkMenuPathApi,
  createMenuApi,
  getAllMenuTreeApi,
} from '#/api/core/menu';
import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

const emit = defineEmits<{
  success: [menuData?: any];
}>();

const appContextStore = useAppContextStore();
const formData = ref<Partial<Menu>>();
const titleSuffix = ref<string>();
const parentMenuPath = ref<string>();
const menuTreeData = ref<any[]>([]);
const visible = ref(false);
const confirmLoading = ref(false);

/**
 * 处理菜单数据，添加 name 字段用于显示
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
  menuTreeData.value = data;
  return processMenuData(data);
}

/**
 * 根据 ID 查找菜单
 */
function findMenuById(menus: any[], id: string): any | null {
  for (const menu of menus) {
    if (menu.id === id) {
      return menu;
    }
    if (menu.children) {
      const found = findMenuById(menu.children, id);
      if (found) return found;
    }
  }
  return null;
}

/**
 * 检查菜单名称是否存在
 */
async function isMenuNameExists(name: string) {
  const result = await checkMenuNameApi(name);
  return result.exists;
}

/**
 * 检查菜单路径是否存在
 */
async function isMenuPathExists(path: string) {
  const result = await checkMenuPathApi(path);
  return result.exists;
}

const schema = computed((): VbenFormSchema[] => [
  {
    component: 'ApiTreeSelect',
    componentProps: {
      api: getMenuListProcessed,
      checkStrictly: true,
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
      valueField: 'id',
      childrenField: 'children',
      async onChange(value: string) {
        // 当选择父菜单时，更新父菜单路径
        if (value && menuTreeData.value.length > 0) {
          const parentMenu = findMenuById(menuTreeData.value, value);
          if (parentMenu?.path) {
            parentMenuPath.value = parentMenu.path;
            // 自动填充路径前缀
            const values = await formApi.getValues();
            const currentPath = values.path;
            if (!currentPath || currentPath === '/') {
              formApi.setFieldValue('path', `${parentMenu.path}/`);
            }
          }
        } else {
          parentMenuPath.value = undefined;
        }
      },
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
    fieldName: 'name',
    label: $t('menu.menuName'),
    rules: z
      .string()
      .min(2, $t('ui.formRules.minLength', [$t('menu.menuName'), 2]))
      .max(30, $t('ui.formRules.maxLength', [$t('menu.menuName'), 30]))
      .refine(
        async (value: string) => {
          return !(await isMenuNameExists(value));
        },
        (value) => ({
          message: $t('ui.formRules.alreadyExists', [
            $t('menu.menuName'),
            value,
          ]),
        }),
      ),
  },
  {
    component: 'Input',
    componentProps() {
      return {
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
        append: () => titleSuffix.value || '',
      };
    },
  },
  {
    component: 'IconPicker',
    componentProps: {
      prefix: 'lucide',
    },
    fieldName: 'icon',
    label: $t('menu.icon'),
  },
  {
    component: 'Input',
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
      .refine(
        async (value: string) => {
          return !(await isMenuPathExists(value));
        },
        (value) => ({
          message: $t('ui.formRules.alreadyExists', [$t('menu.path'), value]),
        }),
      ),
  },
]);

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: schema.value,
  showDefaultActions: false,
});

async function open(data?: Partial<Menu> & { parent_path?: string }) {
  visible.value = true;
  if (data) {
    formData.value = data;

    let parentPath: string | undefined;

    if (data.parent_path) {
      parentPath = data.parent_path;
    } else if (data.parent_id && menuTreeData.value.length > 0) {
      const parentMenu = findMenuById(menuTreeData.value, data.parent_id);
      if (parentMenu?.path) {
        parentPath = parentMenu.path;
      }
    }

    if (parentPath) {
      parentMenuPath.value = parentPath;
    }

    const formValues: Record<string, any> = { ...data };

    if (parentPath && !data.path) {
      formValues.path = `${parentPath}/`;
    }

    await formApi.setValues(formValues);
  } else {
    formApi.resetForm();
    parentMenuPath.value = undefined;
    titleSuffix.value = undefined;
  }
}

defineExpose({
  open,
});

async function onSubmit() {
  const { valid } = await formApi.validate();
  if (valid) {
    confirmLoading.value = true;
    try {
      const data = await formApi.getValues<Partial<Menu>>();
      const menuData = {
        name: data.name!,
        type: data.type || 'catalog',
        path: data.path!,
        parent_id: data.parent_id,
        title: data.title,
        icon: data.icon,
        order: 0,
        application_id: appContextStore.currentApp?.id,
      };

      const result = await createMenuApi(menuData);
      ElMessage.success($t('ui.actionMessage.createSuccess'));
      visible.value = false;

      emit('success', result);
    } catch {
      ElMessage.error($t('ui.actionMessage.createError'));
    } finally {
      confirmLoading.value = false;
    }
  }
}

const getModalTitle = computed(() =>
  $t('ui.actionTitle.create', [$t('menu.name')]),
);
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="getModalTitle"
    :confirm-loading="confirmLoading"
    width="500px"
    @confirm="onSubmit"
  >
    <Form class="mx-4" />
  </ZqDialog>
</template>
