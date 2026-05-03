<script setup lang="ts">
import { Page } from '@vben/common-ui';

import CreateFolderDialog from './components/CreateFolderDialog.vue';
import FileList from './components/FileList.vue';
import FileToolbar from './components/FileToolbar.vue';
</script>

<template>
  <Page auto-content-height>
    <div
      class="bg-background flex h-full w-full flex-col overflow-hidden rounded-[10px]"
    >
      <FileToolbar />
      <div class="flex-1 overflow-hidden">
        <FileList />
      </div>
      <CreateFolderDialog />
    </div>
  </Page>
</template>
