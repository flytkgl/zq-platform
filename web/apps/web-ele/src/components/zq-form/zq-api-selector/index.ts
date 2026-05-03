import { defineAsyncComponent } from 'vue';

export const ZqApiSelect = defineAsyncComponent(() =>
  import('./zq-api-select.vue').then((module) => module.default),
);

export * from './types';
