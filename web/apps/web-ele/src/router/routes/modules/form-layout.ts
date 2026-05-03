import type { RouteRecordRaw } from 'vue-router';

import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      hideInBreadcrumb: true,
      hideInMenu: true,
      hideInTab: true,
      title: 'FormLayout',
    },
    name: 'FormLayoutRoot',
    path: '/form-layout',
    children: [
      // Layout 表单页面 - 新增（主应用）
      {
        name: 'FormLayoutAdd',
        path: ':code/add',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '新增表单',
        },
      },
      // Layout 表单页面 - 编辑（主应用）
      {
        name: 'FormLayoutEdit',
        path: ':code/edit/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '编辑表单',
        },
      },
      // Layout 表单页面 - 查看（主应用）
      {
        name: 'FormLayoutView',
        path: ':code/view/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '查看表单',
        },
      },
    ],
  },
  // 子应用路由
  {
    component: BasicLayout,
    meta: {
      hideInBreadcrumb: true,
      hideInMenu: true,
      hideInTab: true,
      title: 'SubAppFormLayout',
    },
    name: 'SubAppFormLayoutRoot',
    path: '/app/:appCode/form-layout',
    children: [
      // Layout 表单页面 - 新增（子应用）
      {
        name: 'SubAppFormLayoutAdd',
        path: ':code/add',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '新增表单',
        },
      },
      // Layout 表单页面 - 编辑（子应用）
      {
        name: 'SubAppFormLayoutEdit',
        path: ':code/edit/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '编辑表单',
        },
      },
      // Layout 表单页面 - 查看（子应用）
      {
        name: 'SubAppFormLayoutView',
        path: ':code/view/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '查看表单',
        },
      },
    ],
  },
  // 子应用开发模式路由
  {
    component: BasicLayout,
    meta: {
      hideInBreadcrumb: true,
      hideInMenu: true,
      hideInTab: true,
      title: 'SubAppDevFormLayout',
    },
    name: 'SubAppDevFormLayoutRoot',
    path: '/app-dev/:appCode/form-layout',
    children: [
      // Layout 表单页面 - 新增（子应用开发模式）
      {
        name: 'SubAppDevFormLayoutAdd',
        path: ':code/add',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '新增表单',
        },
      },
      // Layout 表单页面 - 编辑（子应用开发模式）
      {
        name: 'SubAppDevFormLayoutEdit',
        path: ':code/edit/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '编辑表单',
        },
      },
      // Layout 表单页面 - 查看（子应用开发模式）
      {
        name: 'SubAppDevFormLayoutView',
        path: ':code/view/:id',
        component: () =>
          import('#/views/online-dev/form-render/form-layout.vue'),
        meta: {
          hideInBreadcrumb: true,
          hideInMenu: true,
          hideInTab: true,
          title: '查看表单',
        },
      },
    ],
  },
];

export default routes;
