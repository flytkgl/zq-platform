<script setup lang="ts">
import type { CSSProperties } from 'vue';

import { computed, shallowRef, useSlots, watchEffect } from 'vue';

import { VbenScrollbar } from '@vben-core/shadcn-ui';

import { useScrollLock } from '@vueuse/core';

import sidebarFooterLogoUrl from '../assets/logo.png';
import { SidebarCollapseButton, SidebarFixedButton } from './widgets';

interface Props {
  /**
   * 折叠区域高度
   * @default 42
   */
  collapseHeight?: number;
  /**
   * 折叠宽度
   * @default 48
   */
  collapseWidth?: number;
  /**
   * 隐藏的dom是否可见
   * @default true
   */
  domVisible?: boolean;
  /**
   * 扩展区域宽度
   */
  extraWidth: number;
  /**
   * 固定扩展区域
   * @default false
   */
  fixedExtra?: boolean;
  /**
   * 头部高度
   */
  headerHeight: number;
  /**
   * 是否侧边混合模式
   * @default false
   */
  isSidebarMixed?: boolean;
  /**
   * 是否垂直双列（sidebar-mixed-nav）；第二列收起时不展示第一列底栏 footer
   * @default false
   */
  isSidebarMixedNav?: boolean;
  /**
   * 是否显示侧边栏品牌标识
   * @default true
   */
  sidebarBranding?: boolean;
  /**
   * 顶部margin
   * @default 60
   */
  marginTop?: number;
  /**
   * 混合菜单宽度
   * @default 80
   */
  mixedWidth?: number;
  /**
   * 顶部padding
   * @default 60
   */
  paddingTop?: number;
  /**
   * 是否显示
   * @default true
   */
  show?: boolean;
  /**
   * 显示折叠按钮
   * @default true
   */
  showCollapseButton?: boolean;
  /**
   * 显示固定按钮
   * @default true
   */
  showFixedButton?: boolean;
  /**
   * 主题
   */
  theme: string;

  /**
   * 宽度
   */
  width: number;
  /**
   * zIndex
   * @default 0
   */
  zIndex?: number;
}

const props = withDefaults(defineProps<Props>(), {
  collapseHeight: 42,
  collapseWidth: 48,
  domVisible: true,
  fixedExtra: false,
  isSidebarMixed: false,
  isSidebarMixedNav: false,
  sidebarBranding: true,
  marginTop: 0,
  mixedWidth: 70,
  paddingTop: 0,
  show: true,
  showCollapseButton: true,
  showFixedButton: true,
  zIndex: 0,
});

const emit = defineEmits<{ leave: [] }>();
const collapse = defineModel<boolean>('collapse');
const extraCollapse = defineModel<boolean>('extraCollapse');
const expandOnHovering = defineModel<boolean>('expandOnHovering');
const expandOnHover = defineModel<boolean>('expandOnHover');
const extraVisible = defineModel<boolean>('extraVisible');

const isLocked = useScrollLock(document.body);
const slots = useSlots();

/** 带连字符的插槽在 useSlots 中键名为 'sidebar-footer'（不是 sidebarFooter） */
const hasSidebarFooterSlot = computed(
  () => Boolean(slots['sidebar-footer'] || slots.sidebarFooter) && props.sidebarBranding,
);

const asideRef = shallowRef<HTMLDivElement | null>();

const hiddenSideStyle = computed((): CSSProperties => calcMenuWidthStyle(true));

const style = computed((): CSSProperties => {
  const { isSidebarMixed, marginTop, paddingTop, zIndex } = props;
  return {
    '--scroll-shadow': 'var(--sidebar)',
    ...calcMenuWidthStyle(false),
    height: `calc(100% - ${marginTop + 12}px)`,
    left: '12px',
    marginTop: `${marginTop}px`,
    paddingTop: `${paddingTop}px`,
    zIndex,
    ...(isSidebarMixed && extraVisible.value ? { transition: 'none' } : {}),
  };
});

const extraStyle = computed((): CSSProperties => {
  const { extraWidth, show, width, zIndex } = props;

  return {
    left: `${width + 12}px`,
    width: extraVisible.value && show ? `${extraWidth}px` : 0,
    zIndex,
  };
});

const extraTitleStyle = computed((): CSSProperties => {
  const { headerHeight } = props;

  return {
    height: `${headerHeight - 1}px`,
  };
});

const contentWidthStyle = computed((): CSSProperties => {
  const { collapseWidth, fixedExtra, isSidebarMixed, mixedWidth } = props;
  if (isSidebarMixed && fixedExtra) {
    return { width: `${collapse.value ? collapseWidth : mixedWidth}px` };
  }
  return {};
});

const contentStyle = computed((): CSSProperties => {
  const { collapseHeight, headerHeight, isSidebarMixed } = props;
  const bottomBar = isSidebarMixed
    ? firstColumnMixedFooterReserve.value
    : collapseHeight;

  return {
    height: `calc(100% - ${headerHeight + bottomBar}px)`,
    paddingTop: '8px',
    ...contentWidthStyle.value,
  };
});

const headerStyle = computed((): CSSProperties => {
  const { headerHeight, isSidebarMixed } = props;

  return {
    ...(isSidebarMixed ? { display: 'flex', justifyContent: 'center' } : {}),
    height: `${headerHeight - 1}px`,
    ...contentWidthStyle.value,
  };
});

/** 第二列有 Powered by 时用更矮底栏；无 footer 时仍用全局 collapseHeight 给图标留位 */
const extraBottomStripHeight = computed(() => {
  if (hasSidebarFooterSlot.value) {
    return Math.min(24, props.collapseHeight);
  }
  return props.collapseHeight;
});

/** 垂直双列第二列折叠（extraCollapse）或完全收起（!extraVisible）时，不在第一列底显示 footer */
const hideSidebarMixedNavFooter = computed(
  () =>
    props.isSidebarMixedNav &&
    (!extraVisible.value || extraCollapse.value),
);

/** 双列且第二列完全收起时，footer 改在第一列底（仅 Header 双列）；垂直双列任意收起态不占位 */
const firstColumnMixedFooterReserve = computed(() => {
  if (!props.isSidebarMixed || extraVisible.value) {
    return 0;
  }
  if (!hasSidebarFooterSlot.value) {
    return 0;
  }
  if (props.isSidebarMixedNav) {
    return 0;
  }
  return extraBottomStripHeight.value;
});

const extraShowsFooterStrip = computed(
  () =>
    hasSidebarFooterSlot.value &&
    extraVisible.value &&
    !hideSidebarMixedNavFooter.value,
);

/** 第二列滚动区底部预留：只有真正显示 Powered by 条时才用矮条，否则用 collapseHeight 给底栏按钮 */
const extraScrollBottomReserve = computed(() =>
  extraShowsFooterStrip.value
    ? extraBottomStripHeight.value
    : props.collapseHeight,
);

/** 有 footer 条时收紧标题区与滚动区间隙 */
const extraContentTailGap = computed(() =>
  extraShowsFooterStrip.value ? 8 : 24,
);

const extraContentStyle = computed((): CSSProperties => {
  const { headerHeight } = props;
  const bottom = extraScrollBottomReserve.value;
  const gap = extraContentTailGap.value;
  return {
    height: `calc(100% - ${headerHeight + bottom + gap}px)`,
  };
});

const extraCollapseStripStyle = computed((): CSSProperties => ({
  height: `${extraBottomStripHeight.value}px`,
}));

const collapseStyle = computed((): CSSProperties => {
  return {
    height: `${props.collapseHeight}px`,
  };
});

watchEffect(() => {
  extraVisible.value = props.fixedExtra ? true : extraVisible.value;
});

function calcMenuWidthStyle(isHiddenDom: boolean): CSSProperties {
  const { extraWidth, fixedExtra, isSidebarMixed, show, width } = props;

  let widthValue =
    width === 0
      ? '0px'
      : `${width + (isSidebarMixed && fixedExtra && extraVisible.value ? extraWidth : 0)}px`;

  const { collapseWidth } = props;

  if (isHiddenDom && expandOnHovering.value && !expandOnHover.value) {
    widthValue = `${collapseWidth}px`;
  }

  return {
    ...(widthValue === '0px' ? { overflow: 'hidden' } : {}),
    flex: `0 0 ${widthValue}`,
    marginLeft: show ? 0 : `-${widthValue}`,
    maxWidth: widthValue,
    minWidth: widthValue,
    width: widthValue,
  };
}

function handleMouseenter(e: MouseEvent) {
  if (e?.offsetX < 10) {
    return;
  }

  // 未开启和未折叠状态不生效
  if (expandOnHover.value) {
    return;
  }
  if (!expandOnHovering.value) {
    collapse.value = false;
  }
  if (props.isSidebarMixed) {
    isLocked.value = true;
  }
  expandOnHovering.value = true;
}

function handleMouseleave() {
  emit('leave');
  if (props.isSidebarMixed) {
    isLocked.value = false;
  }
  if (expandOnHover.value) {
    return;
  }

  expandOnHovering.value = false;
  collapse.value = true;
  extraVisible.value = false;
}
</script>

<template>
  <div
    v-if="domVisible"
    :class="theme"
    :style="hiddenSideStyle"
    class="h-full transition-all duration-150"
  ></div>
  <aside
    :class="[
      theme,
      {
        'bg-sidebar-deep': isSidebarMixed,
        'bg-sidebar': !isSidebarMixed,
      },
    ]"
    :style="style"
    class="fixed left-0 top-0 h-full rounded-lg transition-all duration-150"
    @mouseenter="handleMouseenter"
    @mouseleave="handleMouseleave"
  >
    <div v-if="slots.logo" :style="headerStyle">
      <slot name="logo"></slot>
    </div>
    <VbenScrollbar :style="contentStyle" shadow shadow-border>
      <slot></slot>
    </VbenScrollbar>

    <!-- 仅 Header 双列且第二列未展开：footer 放在第一列；垂直双列第二列收起时不显示 -->
    <div
      v-if="
        isSidebarMixed &&
        !isSidebarMixedNav &&
        !extraVisible &&
        hasSidebarFooterSlot
      "
      :style="extraCollapseStripStyle"
      class="relative w-full shrink-0"
    >
      <div
        class="pointer-events-none absolute inset-0 flex items-center justify-center px-1"
      >
        <div
          class="pointer-events-auto flex min-w-0 max-w-full items-center justify-center"
        >
          <img
            :src="sidebarFooterLogoUrl"
            alt=""
            class="size-3.5 shrink-0 object-contain"
          />
          <slot name="sidebar-footer" :compact="true"></slot>
        </div>
      </div>
    </div>

    <!-- 单列：底部条 左折叠 | 中间自定义 | 右钉住；双列展开时 footer 在第二列底部 -->
    <div
      v-if="!isSidebarMixed"
      :style="collapseStyle"
      class="relative w-full shrink-0"
    >
      <SidebarCollapseButton
        v-if="showCollapseButton"
        v-model:collapsed="collapse"
      />
      <div
        v-if="hasSidebarFooterSlot && sidebarBranding"
        class="pointer-events-none absolute inset-0 flex items-center justify-center px-11"
      >
        <div
          class="pointer-events-auto flex min-w-0 max-w-full items-center justify-center"
        >
          <img
            :src="sidebarFooterLogoUrl"
            alt=""
            class="size-3.5 shrink-0 object-contain"
          />
          <slot :compact="false" name="sidebar-footer"></slot>
        </div>
      </div>
      <SidebarFixedButton
        v-if="!collapse && showFixedButton"
        v-model:expand-on-hover="expandOnHover"
      />
    </div>
    <div
      v-if="isSidebarMixed"
      ref="asideRef"
      :class="{
        // 'border-l': extraVisible,
      }"
      :style="extraStyle"
      class="border-border bg-sidebar fixed overflow-hidden rounded-lg transition-all duration-200"
      style="top: 12px; height: calc(100% - 24px)"
    >
      <SidebarCollapseButton
        v-if="isSidebarMixed && expandOnHover"
        v-model:collapsed="extraCollapse"
      />

      <SidebarFixedButton
        v-if="!extraCollapse"
        v-model:expand-on-hover="expandOnHover"
      />
      <div v-if="!extraCollapse" :style="extraTitleStyle" class="pl-2">
        <slot name="extra-title"></slot>
      </div>
      <VbenScrollbar
        :style="extraContentStyle"
        class="border-border py-2"
        shadow
        shadow-border
      >
        <slot name="extra"></slot>
      </VbenScrollbar>
      <!-- 第二列展开且非「垂直双列+第二列折窄」时：底栏在左折叠与右钉住之间（折窄时易溢出到第一列） -->
      <div
        v-if="extraShowsFooterStrip && sidebarBranding"
        :style="extraCollapseStripStyle"
        class="relative w-full shrink-0"
      >
        <div
          class="pointer-events-none absolute inset-0 flex items-center justify-center px-11"
        >
          <div
            class="pointer-events-auto flex min-w-0 max-w-full items-center justify-center"
          >
            <img
              :src="sidebarFooterLogoUrl"
              alt=""
              class="size-3.5 shrink-0 object-contain"
            />
            <slot :compact="false" name="sidebar-footer"></slot>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
