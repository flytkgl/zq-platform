import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // 表单设计器 - 主应用
  {
    meta: {
      hideInMenu: true,
      title: '表单设计器',
      noBasicLayout: true,
    },
    name: 'FormDesignEditor',
    path: '/online-dev/form-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/form-manager/editor/index.vue'),
  },
  // 表单设计器 - 子应用
  {
    meta: {
      hideInMenu: true,
      title: '表单设计器',
      noBasicLayout: true,
    },
    name: 'SubAppFormDesignEditor',
    path: '/app/:appCode/online-dev/form-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/form-manager/editor/index.vue'),
  },
  // 表单设计器 - 子应用开发模式
  {
    meta: {
      hideInMenu: true,
      title: '表单设计器',
      noBasicLayout: true,
    },
    name: 'SubAppDevFormDesignEditor',
    path: '/app-dev/:appCode/online-dev/form-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/form-manager/editor/index.vue'),
  },
  // 页面设计器 - 主应用
  {
    meta: {
      hideInMenu: true,
      title: '页面设计器',
      noBasicLayout: true,
    },
    name: 'PageDesignEditor',
    path: '/online-dev/page-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/page-manager/editor/index.vue'),
  },
  // 页面设计器 - 子应用
  {
    meta: {
      hideInMenu: true,
      title: '页面设计器',
      noBasicLayout: true,
    },
    name: 'SubAppPageDesignEditor',
    path: '/app/:appCode/online-dev/page-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/page-manager/editor/index.vue'),
  },
  // 页面设计器 - 子应用开发模式
  {
    meta: {
      hideInMenu: true,
      title: '页面设计器',
      noBasicLayout: true,
    },
    name: 'SubAppDevPageDesignEditor',
    path: '/app-dev/:appCode/online-dev/page-manager/editor/:id',
    component: () =>
      import('#/views/online-dev/page-manager/editor/index.vue'),
  },
];

export default routes;
