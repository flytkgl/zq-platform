import { defineAsyncComponent } from 'vue';

export const UserSelector = defineAsyncComponent(() =>
  import('./user-selector.vue').then((module) => module.default),
);

export * from './types';
