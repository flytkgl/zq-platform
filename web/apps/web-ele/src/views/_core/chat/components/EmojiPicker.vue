<script setup lang="ts">
import { ref } from 'vue';

import { ElScrollbar } from 'element-plus';

const emit = defineEmits<{
  select: [emoji: string];
}>();

const activeCategory = ref(0);

const categories = [
  {
    key: 'smileys',
    icon: '😀',
    emojis: [
      '😀',
      '😃',
      '😄',
      '😁',
      '😆',
      '😅',
      '🤣',
      '😂',
      '🙂',
      '😉',
      '😊',
      '😇',
      '🥰',
      '😍',
      '🤩',
      '😘',
      '😗',
      '😚',
      '😙',
      '🥲',
      '😋',
      '😛',
      '😜',
      '🤪',
      '😝',
      '🤑',
      '🤗',
      '🤭',
      '🤫',
      '🤔',
      '🫡',
      '🤐',
      '🤨',
      '😐',
      '😑',
      '😶',
      '🫥',
      '😏',
      '😒',
      '🙄',
      '😬',
      '🤥',
      '😌',
      '😔',
      '😪',
      '🤤',
      '😴',
      '😷',
      '🤒',
      '🤕',
      '🤢',
      '🤮',
      '🥵',
      '🥶',
      '🥴',
      '😵',
      '🤯',
      '🤠',
      '🥳',
      '🥸',
      '😎',
      '🤓',
      '🧐',
      '😕',
      '🫤',
      '😟',
      '🙁',
      '😮',
      '😯',
      '😲',
      '😳',
      '🥺',
      '🥹',
      '😦',
      '😧',
      '😨',
      '😰',
      '😥',
      '😢',
      '😭',
      '😱',
      '😖',
      '😣',
      '😞',
      '😓',
      '😩',
      '😫',
      '🥱',
    ],
  },
  {
    key: 'gestures',
    icon: '👋',
    emojis: [
      '👋',
      '🤚',
      '🖐️',
      '✋',
      '🖖',
      '🫱',
      '🫲',
      '🫳',
      '🫴',
      '👌',
      '🤌',
      '🤏',
      '✌️',
      '🤞',
      '🫰',
      '🤟',
      '🤘',
      '🤙',
      '👈',
      '👉',
      '👆',
      '🖕',
      '👇',
      '☝️',
      '🫵',
      '👍',
      '👎',
      '✊',
      '👊',
      '🤛',
      '🤜',
      '👏',
      '🙌',
      '🫶',
      '👐',
      '🤲',
      '🤝',
      '🙏',
      '💪',
      '🦾',
    ],
  },
  {
    key: 'hearts',
    icon: '❤️',
    emojis: [
      '❤️',
      '🧡',
      '💛',
      '💚',
      '💙',
      '💜',
      '🖤',
      '🤍',
      '🤎',
      '💔',
      '❤️‍🔥',
      '❤️‍🩹',
      '❣️',
      '💕',
      '💞',
      '💓',
      '💗',
      '💖',
      '💘',
      '💝',
      '💟',
      '♥️',
      '💋',
      '💯',
      '💢',
      '💥',
      '💫',
      '💦',
      '💨',
      '🕳️',
      '💣',
      '💬',
    ],
  },
  {
    key: 'objects',
    icon: '🎉',
    emojis: [
      '🎉',
      '🎊',
      '🎈',
      '🎁',
      '🎀',
      '🏆',
      '🥇',
      '🥈',
      '🥉',
      '⚽',
      '🏀',
      '🎯',
      '🎮',
      '🎲',
      '🧩',
      '🎵',
      '🎶',
      '🔔',
      '📢',
      '💡',
      '🔥',
      '⭐',
      '🌟',
      '✨',
      '⚡',
      '☀️',
      '🌈',
      '☁️',
      '❄️',
      '🌸',
      '🍀',
      '🌺',
    ],
  },
  {
    key: 'food',
    icon: '🍕',
    emojis: [
      '🍕',
      '🍔',
      '🍟',
      '🌭',
      '🍿',
      '🧁',
      '🍰',
      '🎂',
      '🍩',
      '🍪',
      '🍫',
      '🍬',
      '🍭',
      '☕',
      '🍵',
      '🧋',
      '🍺',
      '🍻',
      '🥂',
      '🍷',
      '🍸',
      '🍹',
      '🧃',
      '🍎',
      '🍊',
      '🍋',
      '🍌',
      '🍉',
      '🍇',
      '🍓',
      '🫐',
      '🍑',
    ],
  },
];

function handleSelect(emoji: string) {
  emit('select', emoji);
}
</script>

<template>
  <div class="emoji-picker">
    <!-- 分类标签 -->
    <div class="emoji-tabs">
      <button
        v-for="(cat, idx) in categories"
        :key="cat.key"
        class="emoji-tab"
        :class="{ 'emoji-tab--active': activeCategory === idx }"
        @click="activeCategory = idx"
      >
        {{ cat.icon }}
      </button>
    </div>
    <!-- 表情网格 -->
    <ElScrollbar height="200px">
      <div class="emoji-grid">
        <button
          v-for="emoji in categories[activeCategory]!.emojis"
          :key="emoji"
          class="emoji-item"
          :title="emoji"
          @click="handleSelect(emoji)"
        >
          {{ emoji }}
        </button>
      </div>
    </ElScrollbar>
  </div>
</template>

<style scoped>
.emoji-picker {
  width: 320px;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.emoji-tabs {
  display: flex;
  gap: 2px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.emoji-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 28px;
  padding: 0;
  font-size: 16px;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 6px;
  outline: none;
  transition: background 0.15s;
}

.emoji-tab:hover {
  background: var(--el-fill-color-light);
}

.emoji-tab--active {
  background: var(--el-color-primary-light-9);
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 2px;
  padding: 6px 8px;
}

.emoji-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  font-size: 20px;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 6px;
  outline: none;
  transition: all 0.15s;
}

.emoji-item:hover {
  background: var(--el-fill-color-light);
  transform: scale(1.2);
}
</style>
