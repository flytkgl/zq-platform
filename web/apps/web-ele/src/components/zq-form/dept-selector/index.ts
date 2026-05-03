import { defineAsyncComponent } from 'vue';

export const DeptSelector = defineAsyncComponent(() =>
  import('./dept-selector.vue').then((module) => module.default),
);

export * from './types';
