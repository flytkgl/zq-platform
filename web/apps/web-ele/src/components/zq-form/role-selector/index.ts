import { defineAsyncComponent } from 'vue';

export const RoleSelector = defineAsyncComponent(() =>
  import('./role-selector.vue').then((module) => module.default),
);
