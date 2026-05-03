<script setup lang="ts">
import { computed, ref } from 'vue';

import { ExternalLink, Link, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import { NodeViewWrapper } from '@tiptap/vue-3';

import { getLinkPreview } from '#/api/core/link-preview';

const props = defineProps<{
  deleteNode: () => void;
  node: any;
  selected: boolean;
  updateAttributes: (attrs: Record<string, any>) => void;
}>();

const urlInput = ref('');
const loading = ref(false);

const hasUrl = computed(() => !!props.node.attrs.url);

const displayDomain = computed(() => {
  try {
    const u = new URL(props.node.attrs.url);
    return u.hostname;
  } catch {
    return '';
  }
});

async function handleEmbed() {
  const raw = urlInput.value.trim();
  if (!raw) return;

  const url = /^https?:\/\//.test(raw) ? raw : `https://${raw}`;

  loading.value = true;
  try {
    const meta = await getLinkPreview(url);
    props.updateAttributes({
      url: meta.url || url,
      title: meta.title || null,
      description: meta.description || null,
      image: meta.image || null,
      favicon: meta.favicon || null,
      siteName: meta.site_name || null,
    });
  } catch {
    props.updateAttributes({ url });
  } finally {
    loading.value = false;
  }
}

function handleOpen() {
  if (props.node.attrs.url) {
    window.open(props.node.attrs.url, '_blank', 'noopener');
  }
}

function handleDelete() {
  props.deleteNode();
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault();
    handleEmbed();
  }
}
</script>

<template>
  <NodeViewWrapper
    class="zq-embed"
    :class="{ 'zq-embed--empty': !hasUrl }"
    data-type="embed"
  >
    <!-- 输入态 -->
    <div v-if="!hasUrl" class="zq-embed__input-wrapper">
      <div class="zq-embed__input-row">
        <Link class="zq-embed__link-icon" />
        <input
          v-model="urlInput"
          class="zq-embed__input"
          :placeholder="$t('zq-editor.embed.placeholder')"
          :disabled="loading"
          @keydown="onKeydown"
        />
        <button
          class="zq-embed__submit"
          :disabled="!urlInput.trim() || loading"
          @click="handleEmbed"
        >
          {{ loading ? $t('zq-editor.embed.loading') : $t('zq-editor.embed.submit') }}
        </button>
      </div>
    </div>

    <!-- 卡片态 -->
    <div
      v-else
      class="zq-embed__card"
      @click="handleOpen"
    >
      <div class="zq-embed__content">
        <div class="zq-embed__title">
          {{ node.attrs.title || node.attrs.url }}
        </div>
        <div v-if="node.attrs.description" class="zq-embed__desc">
          {{ node.attrs.description }}
        </div>
        <div class="zq-embed__meta">
          <img
            v-if="node.attrs.favicon"
            :src="node.attrs.favicon"
            class="zq-embed__favicon"
            @error="($event.target as HTMLImageElement).style.display = 'none'"
          />
          <span class="zq-embed__domain">
            {{ node.attrs.siteName || displayDomain }}
          </span>
        </div>
      </div>
      <img
        v-if="node.attrs.image"
        :src="node.attrs.image"
        class="zq-embed__thumbnail"
        @error="($event.target as HTMLImageElement).style.display = 'none'"
      />
      <div class="zq-embed__actions" @click.stop>
        <button
          class="zq-embed__action-btn"
          :title="$t('zq-editor.embed.open')"
          @click="handleOpen"
        >
          <ExternalLink class="h-3.5 w-3.5" />
        </button>
        <button
          class="zq-embed__action-btn zq-embed__action-btn--danger"
          :title="$t('zq-editor.embed.delete')"
          @click="handleDelete"
        >
          <Trash2 class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  </NodeViewWrapper>
</template>

<style scoped>
.zq-embed {
  margin: 8px 0;
}

.zq-embed__input-wrapper {
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
}

.zq-embed__input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zq-embed__link-icon {
  width: 18px;
  height: 18px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.zq-embed__input {
  flex: 1;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.8125rem;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
  transition: border-color 0.2s;
}

.zq-embed__input:focus {
  border-color: var(--el-color-primary);
}

.zq-embed__submit {
  flex-shrink: 0;
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: var(--el-color-primary);
  color: var(--el-color-white);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.zq-embed__submit:hover {
  opacity: 0.85;
}

.zq-embed__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.zq-embed__card {
  display: flex;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
  background: var(--el-bg-color);
}

.zq-embed__card:hover {
  border-color: var(--el-border-color);
  box-shadow: var(--el-box-shadow-lighter);
}

.zq-embed__content {
  flex: 1;
  padding: 14px 16px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.zq-embed__title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.zq-embed__desc {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.zq-embed__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.zq-embed__favicon {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  flex-shrink: 0;
}

.zq-embed__domain {
  font-size: 0.6875rem;
  color: var(--el-text-color-placeholder);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zq-embed__thumbnail {
  width: 120px;
  height: auto;
  max-height: 100px;
  object-fit: cover;
  flex-shrink: 0;
}

.zq-embed__actions {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.zq-embed__card:hover .zq-embed__actions {
  opacity: 1;
}

.zq-embed__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  box-shadow: var(--el-box-shadow-lighter);
  transition: background-color 0.15s, color 0.15s;
}

.zq-embed__action-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.zq-embed__action-btn--danger:hover {
  color: var(--el-color-danger);
}
</style>
