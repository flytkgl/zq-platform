<script lang="ts" setup>
import { About } from '@vben/common-ui';
import { $t } from '@vben/locales';

defineOptions({ name: 'About' });

const labels = {
  author: $t('about.author'),
  basicInfo: $t('about.basicInfo'),
  buildTime: $t('about.buildTime'),
  devDependencies: $t('about.devDependencies'),
  docUrl: $t('about.docUrl'),
  github: $t('about.github'),
  homepage: $t('about.homepage'),
  license: $t('about.license'),
  previewUrl: $t('about.previewUrl'),
  productionDependencies: $t('about.productionDependencies'),
  version: $t('about.version'),
  viewDetails: $t('about.viewDetails'),
};
</script>

<template>
  <About :labels="labels" />
</template>
