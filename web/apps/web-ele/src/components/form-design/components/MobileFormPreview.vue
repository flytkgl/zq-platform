<script setup lang="ts">
import type { FormItemSchema } from '../store/formDesignStore';

import { computed, ref } from 'vue';

defineOptions({ name: 'MobileFormPreview' });
const props = defineProps<{ isNested?: boolean; items: FormItemSchema[] }>();

const SKIP_TYPES = new Set([
  'color',
  'cron-selector',
  'current-datetime',
  'divider',
  'html',
  'money-input',
  'spacer',
  'text',
  'timeline',
  'tip',
]);
const STANDALONE_TYPES = new Set([
  'alert',
  'collapse',
  'qrcode-generator',
  'signature-pad',
  'steps',
  'sub-table',
  'tabs',
  'title',
]);
const TAG_SELECTOR_TYPES = new Set([
  'dept-selector',
  'form-selector',
  'post-selector',
  'role-selector',
  'table-selector',
  'user-selector',
]);
const PICKER_TYPES = new Set([
  'cascader',
  'date',
  'date-picker',
  'region-selector',
  'select',
  'time',
  'time-picker',
  'tree-select',
]);

function flattenItems(items: FormItemSchema[]): FormItemSchema[] {
  const r: FormItemSchema[] = [];
  for (const item of items) {
    if (SKIP_TYPES.has(item.type)) continue;
    if (item.type === 'grid') {
      // 按行渲染：先遍历行索引，再遍历列
      const columns = item.columns || [];
      const maxRows = Math.max(...columns.map((col: any) => (col.children || []).length));
      for (let rowIndex = 0; rowIndex < maxRows; rowIndex++) {
        for (const col of columns) {
          const child = (col.children || [])[rowIndex];
          if (child && !SKIP_TYPES.has(child.type)) {
            r.push(child);
          }
        }
      }
    } else r.push(item);
  }
  return r;
}

type Group =
  | { item: FormItemSchema; kind: 'standalone' }
  | { items: FormItemSchema[]; kind: 'cells' };

const groups = computed<Group[]>(() => {
  const flat = flattenItems(props.items);
  const result: Group[] = [];
  let buf: FormItemSchema[] = [];
  const flush = () => {
    if (buf.length > 0) {
      result.push({ kind: 'cells', items: [...buf] });
      buf = [];
    }
  };
  for (const item of flat) {
    if (STANDALONE_TYPES.has(item.type)) {
      flush();
      result.push({ kind: 'standalone', item });
    } else buf.push(item);
  }
  flush();
  return result;
});

const tabMap = ref<Record<string, number>>({});
const stepMap = ref<Record<string, number>>({});
const colMap = ref<Record<string, Set<number>>>({});
function getTab(id: string) {
  if (tabMap.value[id] === undefined) tabMap.value[id] = 0;
  return tabMap.value[id];
}
function setTab(id: string, i: number) {
  tabMap.value[id] = i;
}
function getStep(id: string) {
  if (stepMap.value[id] === undefined) stepMap.value[id] = 0;
  return stepMap.value[id];
}
function colOpen(id: string, i: number) {
  if (!colMap.value[id]) colMap.value[id] = new Set([0]);
  return colMap.value[id].has(i);
}
function togCol(id: string, i: number) {
  if (!colMap.value[id]) colMap.value[id] = new Set([0]);
  const s = colMap.value[id];
  if (s.has(i)) s.delete(i);
  else s.add(i);
  colMap.value = { ...colMap.value };
}
function ph(item: FormItemSchema) {
  return item.props?.placeholder || `请输入${item.label}`;
}
function sph(item: FormItemSchema) {
  return item.props?.placeholder || `请选择${item.label}`;
}
function req(item: FormItemSchema) {
  return (
    item.props?.required ||
    ((item as any).rules || []).some((r: any) => r.required)
  );
}
function isLast(items: FormItemSchema[], idx: number) {
  return idx === items.length - 1;
}
</script>

<template>
  <div class="mp" :class="{ 'mp--nested': isNested }">
    <template v-for="(group, gi) in groups" :key="gi">
      <!-- standalone 独立卡片 -->
      <template v-if="group.kind === 'standalone'">
        <div
          v-if="group.item.type === 'title'"
          class="mp-title-card"
          :class="`mp-title-card--${group.item.props?.theme || 'primary'}`"
        >
          <div v-if="group.item.props?.showBar" class="mp-title-bar"></div>
          <span class="mp-title-text">{{
            group.item.props?.text || group.item.label
          }}</span>
        </div>
        <div
          v-else-if="group.item.type === 'alert'"
          class="mp-alert"
          :class="`mp-alert--${group.item.props?.type || 'info'}`"
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            style="flex-shrink: 0; margin-top: 1px"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>
            <div class="mp-alert-title">
              {{ group.item.props?.title || group.item.label }}
            </div>
            <div v-if="group.item.props?.description" class="mp-alert-desc">
              {{ group.item.props.description }}
            </div>
          </div>
        </div>
        <div
          v-else-if="group.item.type === 'tabs'"
          class="mp-card mp-tabs-wrap"
        >
          <div
            class="mp-tabs-nav"
            :class="
              group.item.props?.type === 'card' ||
              group.item.props?.type === 'border-card'
                ? 'mp-tabs-nav--card'
                : 'mp-tabs-nav--line'
            "
          >
            <div
              v-for="(tab, ti) in group.item.items || []"
              :key="ti"
              class="mp-tab"
              :class="{ 'mp-tab--active': getTab(group.item.id) === ti }"
              @click="setTab(group.item.id, ti)"
            >
              {{ tab.label }}
            </div>
            <div
              v-if="
                group.item.props?.type !== 'card' &&
                group.item.props?.type !== 'border-card'
              "
              class="mp-tab-line"
              :style="{
                width: `${100 / Math.max((group.item.items || []).length, 1)}%`,
                left: `${(100 / Math.max((group.item.items || []).length, 1)) * getTab(group.item.id)}%`,
              }"
            ></div>
          </div>
          <div class="mp-tabs-content">
            <MobileFormPreview
              :items="
                (group.item.items || [])[getTab(group.item.id)]?.children || []
              "
              :is-nested="true"
            />
          </div>
        </div>
        <div
          v-else-if="group.item.type === 'steps'"
          class="mp-card mp-steps-wrap"
        >
          <div class="mp-steps-nav">
            <div
              v-for="(step, si) in group.item.items || []"
              :key="si"
              class="mp-step-item"
            >
              <div
                class="mp-step-icon"
                :class="
                  si < getStep(group.item.id)
                    ? 'mp-step-icon--done'
                    : si === getStep(group.item.id)
                      ? 'mp-step-icon--active'
                      : 'mp-step-icon--wait'
                "
              >
                <svg
                  v-if="si < getStep(group.item.id)"
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  stroke-width="3"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span v-else class="mp-step-num">{{ si + 1 }}</span>
              </div>
              <span
                class="mp-step-title"
                :class="
                  si === getStep(group.item.id)
                    ? 'mp-step-title--active'
                    : si < getStep(group.item.id)
                      ? 'mp-step-title--done'
                      : ''
                "
                >{{ step.title || step.label }}</span
              >
              <div
                v-if="si < (group.item.items || []).length - 1"
                class="mp-step-line"
                :class="{ 'mp-step-line--done': si < getStep(group.item.id) }"
              ></div>
            </div>
          </div>
          <div class="mp-steps-content">
            <MobileFormPreview
              :items="
                (group.item.items || [])[getStep(group.item.id)]?.children || []
              "
              :is-nested="true"
            />
          </div>
        </div>
        <div v-else-if="group.item.type === 'collapse'" class="mp-card">
          <div
            v-for="(panel, pi) in group.item.items || []"
            :key="pi"
            class="mp-collapse-item"
            :class="{
              'mp-collapse-item--last':
                pi === (group.item.items || []).length - 1,
            }"
          >
            <div class="mp-collapse-header" @click="togCol(group.item.id, pi)">
              <span class="mp-collapse-title">{{
                panel.title || panel.label
              }}</span>
              <svg
                class="mp-collapse-arrow mp-collapse-arrow-svg"
                :class="{ 'mp-collapse-arrow--up': colOpen(group.item.id, pi) }"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
            <div
              class="mp-collapse-body"
              :class="{ 'mp-collapse-body--open': colOpen(group.item.id, pi) }"
            >
              <MobileFormPreview
                :items="panel.children || []"
                :is-nested="true"
              />
            </div>
          </div>
        </div>
        <div v-else-if="group.item.type === 'sub-table'" class="mp-subtable">
          <div class="mp-subtable-header">
            <span class="mp-subtable-title">{{ group.item.label }}</span>
          </div>
          <div class="mp-subtable-list">
            <!-- 示例第一条记录 -->
            <div class="mp-subtable-card">
              <div class="mp-subtable-card-header">
                <div class="mp-subtable-tag">#1</div>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="mp-icon-danger"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6l-1 14H6L5 6" />
                  <path d="M10 11v6M14 11v6" />
                  <path d="M9 6V4h6v2" />
                </svg>
              </div>
              <div class="mp-subtable-card-body">
                <template
                  v-for="(child, ci) in (group.item.children || []).slice(0, 4)"
                  :key="child.id"
                >
                  <div v-if="TAG_SELECTOR_TYPES.has(child.type)" class="mp-tag-sel" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <div class="mp-tag-sel__label"><span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span></div>
                    <div class="mp-tag-sel__content"><div class="mp-tag-add"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></div></div>
                  </div>
                  <div v-else-if="child.type==='textarea'" class="mp-cell mp-cell--col" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <div class="mp-cell-lr"><span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span></div>
                    <div class="mp-textarea-body">{{ph(child)}}</div>
                  </div>
                  <div v-else-if="child.type==='radio'" class="mp-cell mp-cell--col" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <div class="mp-cell-lr"><span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span></div>
                    <div class="mp-options">
                      <div v-for="(opt,oi) in (child.options||[]).slice(0,5)" :key="oi" class="mp-opt-item">
                        <div class="mp-radio-icon" :class="{'mp-radio-icon--on':oi===0}"><div v-if="oi===0" class="mp-radio-dot"></div></div>
                        <span class="mp-opt-label">{{opt.label}}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="child.type==='checkbox'" class="mp-cell mp-cell--col" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <div class="mp-cell-lr"><span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span></div>
                    <div class="mp-options">
                      <div v-for="(opt,oi) in (child.options||[]).slice(0,5)" :key="oi" class="mp-opt-item">
                        <div class="mp-cb-icon" :class="{'mp-cb-icon--on':oi===0}"><svg v-if="oi===0" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg></div>
                        <span class="mp-opt-label">{{opt.label}}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="child.type==='switch'" class="mp-cell" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span>
                    <div class="mp-switch"><div class="mp-switch-node"></div></div>
                  </div>
                  <div v-else-if="child.type==='input-number'||child.type==='number'" class="mp-cell" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span>
                    <div class="mp-stepper"><div class="mp-stepper-btn">-</div><span class="mp-stepper-val">{{child.props?.min??0}}</span><div class="mp-stepper-btn">+</div></div>
                  </div>
                  <div v-else-if="child.type==='image-selector'||child.type==='file-selector'" class="mp-cell mp-cell--col" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <div class="mp-cell-lr"><span v-if="req(child)" class="mp-req">*</span><span class="mp-label">{{child.label}}</span></div>
                    <div class="mp-upload"><div class="mp-upload-btn"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></div></div>
                  </div>
                  <div v-else-if="['code-generator','formula-input','linked-field','current-user'].includes(child.type)" class="mp-cell" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <span class="mp-label">{{child.label}}</span><span class="mp-value">自动填充</span>
                  </div>
                  <div v-else class="mp-cell" :class="{'mp-row-last':ci===(group.item.children||[]).slice(0,4).length-1}">
                    <span v-if="req(child)" class="mp-req">*</span>
                    <span class="mp-label">{{child.label}}</span>
                    <span class="mp-placeholder">{{PICKER_TYPES.has(child.type)?sph(child):ph(child)}}</span>
                    <svg v-if="PICKER_TYPES.has(child.type)" class="mp-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                  </div>
                </template>
              </div>
            </div>
            <!-- 添加按钮 -->
            <div class="mp-subtable-add-btn">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>添加</span>
            </div>
          </div>
        </div>
        <!-- 签名组件 -->
        <div v-else-if="group.item.type === 'signature-pad'" class="mp-signature">
          <div class="mp-signature-label">
            <span v-if="req(group.item)" class="mp-req">*</span>
            <span>{{ group.item.label }}</span>
          </div>
          <div class="mp-signature-box">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              <path d="m15 5 4 4"/>
            </svg>
            <span class="mp-signature-hint">点击进入签名</span>
          </div>
        </div>
        <!-- 二维码组件 -->
        <div v-else-if="group.item.type === 'qrcode-generator'" class="mp-qrcode">
          <div class="mp-qrcode-label">
            <span v-if="req(group.item)" class="mp-req">*</span>
            <span>{{ group.item.label }}</span>
          </div>
          <div class="mp-qrcode-box">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <rect width="5" height="5" x="3" y="3" rx="1"/>
              <rect width="5" height="5" x="16" y="3" rx="1"/>
              <rect width="5" height="5" x="3" y="16" rx="1"/>
              <path d="M21 16h-3a2 2 0 0 0-2 2v3"/>
              <path d="M21 21v.01"/>
              <path d="M12 7v3a2 2 0 0 1-2 2H7"/>
              <path d="M3 12h.01"/>
              <path d="M12 3h.01"/>
              <path d="M12 16v.01"/>
              <path d="M16 12h1"/>
              <path d="M21 12v.01"/>
              <path d="M12 21v-1"/>
            </svg>
          </div>
        </div>
      </template>

      <!-- cells 分组：共享一个圆角卡片 -->
      <div v-else class="mp-card">
        <template v-for="(item, ii) in group.items" :key="item.id">
          <div
            v-if="TAG_SELECTOR_TYPES.has(item.type)"
            class="mp-tag-sel"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-tag-sel__label">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-tag-sel__content">
              <div class="mp-tag-add">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="mp-icon-muted"
                >
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </div>
            </div>
          </div>
          <div
            v-else-if="item.type === 'textarea'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-textarea-body">{{ ph(item) }}</div>
          </div>
          <div
            v-else-if="item.type === 'radio'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-options">
              <div
                v-for="(opt, oi) in (item.options || []).slice(0, 5)"
                :key="oi"
                class="mp-opt-item"
              >
                <div
                  class="mp-radio-icon"
                  :class="{ 'mp-radio-icon--on': oi === 0 }"
                >
                  <div v-if="oi === 0" class="mp-radio-dot"></div>
                </div>
                <span class="mp-opt-label">{{ opt.label }}</span>
              </div>
            </div>
          </div>
          <div
            v-else-if="item.type === 'checkbox'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-options">
              <div
                v-for="(opt, oi) in (item.options || []).slice(0, 5)"
                :key="oi"
                class="mp-opt-item"
              >
                <div class="mp-cb-icon" :class="{ 'mp-cb-icon--on': oi === 0 }">
                  <svg
                    v-if="oi === 0"
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="3"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <span class="mp-opt-label">{{ opt.label }}</span>
              </div>
            </div>
          </div>
          <div
            v-else-if="item.type === 'rate'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-rate">
              <svg
                v-for="i in item.props?.max || 5"
                :key="i"
                width="22"
                height="22"
                viewBox="0 0 24 24"
                :class="i <= 3 ? 'mp-star--on' : 'mp-star--off'"
                stroke-width="1.5"
              >
                <polygon
                  points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                />
              </svg>
            </div>
          </div>
          <div
            v-else-if="item.type === 'slider'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-slider-wrap">
              <div class="mp-slider-track"></div>
              <div class="mp-slider-fill" style="width: 40%"></div>
              <div class="mp-slider-thumb" style="left: 40%"></div>
            </div>
          </div>
          <div
            v-else-if="
              item.type === 'image-selector' || item.type === 'file-selector'
            "
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-upload">
              <div class="mp-upload-btn">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </div>
            </div>
          </div>
          <div
            v-else-if="item.type === 'ai-image-ocr'"
            class="mp-cell mp-cell--col mp-ocr-cell"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
              <span v-if="item.aiOcrConfig?.enabled" class="mp-ocr-badge">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                AI
              </span>
            </div>
            <div class="mp-ocr-upload">
              <div class="mp-ocr-upload-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <div class="mp-ocr-upload-text">点击上传文件进行AI识别</div>
              <div class="mp-ocr-tags">
                <span class="mp-ocr-tag mp-ocr-tag--primary">{{ item.aiOcrConfig?.templateType || 'custom' }}</span>
                <span class="mp-ocr-tag mp-ocr-tag--info">{{ (item.aiOcrConfig?.acceptFileTypes || ['image']).join(' / ') }}</span>
              </div>
            </div>
          </div>
          <div
            v-else-if="item.type === 'rich-text'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-richtext">{{ ph(item) }}</div>
          </div>
          <!-- 签名组件 -->
          <div
            v-else-if="item.type === 'signature-pad'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span v-if="req(item)" class="mp-req">*</span
              ><span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-signature">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9"/>
                <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>
              </svg>
              <span class="mp-signature-text">{{ ph(item) || '点击签名' }}</span>
            </div>
          </div>
          <!-- 二维码组件 -->
          <div
            v-else-if="item.type === 'qrcode-generator'"
            class="mp-cell mp-cell--col"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <div class="mp-cell-lr">
              <span class="mp-label">{{ item.label }}</span>
            </div>
            <div class="mp-qrcode">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                <rect width="5" height="5" x="3" y="3" rx="1"/>
                <rect width="5" height="5" x="16" y="3" rx="1"/>
                <rect width="5" height="5" x="3" y="16" rx="1"/>
                <path d="M21 16h-3a2 2 0 0 0-2 2v3"/>
                <path d="M21 21v.01"/>
                <path d="M12 7v3a2 2 0 0 1-2 2H7"/>
                <path d="M3 12h.01"/>
                <path d="M12 3h.01"/>
                <path d="M12 16v.01"/>
                <path d="M16 12h1"/>
                <path d="M21 12v.01"/>
                <path d="M12 21v-1"/>
              </svg>
            </div>
          </div>
          <div
            v-else-if="item.type === 'switch'"
            class="mp-cell"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <span v-if="req(item)" class="mp-req">*</span
            ><span class="mp-label">{{ item.label }}</span>
            <div class="mp-switch"><div class="mp-switch-node"></div></div>
          </div>
          <div
            v-else-if="item.type === 'input-number' || item.type === 'number'"
            class="mp-cell"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <span v-if="req(item)" class="mp-req">*</span
            ><span class="mp-label">{{ item.label }}</span>
            <div class="mp-stepper">
              <div class="mp-stepper-btn">-</div>
              <span class="mp-stepper-val">{{ item.props?.min ?? 0 }}</span>
              <div class="mp-stepper-btn">+</div>
            </div>
          </div>
          <div
            v-else-if="
              [
                'code-generator',
                'formula-input',
                'linked-field',
                'current-user',
              ].includes(item.type)
            "
            class="mp-cell"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <span class="mp-label">{{ item.label }}</span><span class="mp-value">自动填充</span>
          </div>
          <div
            v-else
            class="mp-cell"
            :class="{ 'mp-row-last': isLast(group.items, ii) }"
          >
            <span v-if="req(item)" class="mp-req">*</span>
            <span class="mp-label">{{ item.label }}</span>
            <span class="mp-placeholder">{{
              PICKER_TYPES.has(item.type) ? sph(item) : ph(item)
            }}</span>
            <svg
              v-if="PICKER_TYPES.has(item.type)"
              class="mp-chevron"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
.mp {
  background: var(--el-fill-color-light);
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
  font-size: 14px;
  padding: 12px 0;
}
.mp--nested {
  padding: 0;
  background: transparent;
}

/* 分组圆角卡片：两边 12px 间距，下方 10px 间距 */
.mp-card {
  background: var(--el-bg-color);
  border-radius: 20px;
  margin: 0 12px 10px;
  overflow: hidden;
}

/* 行分割线：用 mp-row-last 控制最后一行不显示 */
.mp-cell,
.mp-tag-sel {
  position: relative;
}
.mp-cell::after,
.mp-tag-sel::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 16px;
  right: 16px;
  height: 0.5px;
  background: var(--el-border-color-lighter);
}
.mp-row-last.mp-cell::after,
.mp-row-last.mp-tag-sel::after {
  display: none;
}

/* cell 行 */
.mp-cell {
  display: flex;
  align-items: center;
  padding: 13px 16px;
  min-height: 48px;
}
.mp-cell--col {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}
.mp-cell-lr {
  display: flex;
  align-items: center;
}
.mp-req {
  color: var(--el-color-danger);
  font-size: 13px;
  margin-right: 2px;
  flex-shrink: 0;
}
.mp-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
  width: 90px;
  flex-shrink: 0;
}
.mp-placeholder {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-placeholder);
  text-align: right;
}
.mp-value {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  text-align: right;
}
.mp-chevron {
  flex-shrink: 0;
  margin-left: 4px;
  color: var(--el-text-color-placeholder);
}

/* title */
.mp-title-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  margin: 0 12px 10px;
  border-radius: 20px;
  overflow: hidden;
}
.mp-title-card--primary {
  background: var(--el-color-primary-light-9);
}
.mp-title-card--primary .mp-title-bar {
  background: var(--el-color-primary);
}
.mp-title-card--primary .mp-title-text {
  color: var(--el-color-primary);
}
.mp-title-card--success {
  background: var(--el-color-success-light-9);
}
.mp-title-card--success .mp-title-bar {
  background: var(--el-color-success);
}
.mp-title-card--success .mp-title-text {
  color: var(--el-color-success);
}
.mp-title-card--warning {
  background: var(--el-color-warning-light-9);
}
.mp-title-card--warning .mp-title-bar {
  background: var(--el-color-warning);
}
.mp-title-card--warning .mp-title-text {
  color: var(--el-color-warning);
}
.mp-title-card--danger {
  background: var(--el-color-danger-light-9);
}
.mp-title-card--danger .mp-title-bar {
  background: var(--el-color-danger);
}
.mp-title-card--danger .mp-title-text {
  color: var(--el-color-danger);
}
.mp-title-card--info {
  background: var(--el-fill-color);
}
.mp-title-card--info .mp-title-bar {
  background: var(--el-text-color-secondary);
}
.mp-title-card--info .mp-title-text {
  color: var(--el-text-color-secondary);
}
.mp-title-bar {
  width: 3px;
  height: 16px;
  border-radius: 2px;
  flex-shrink: 0;
}
.mp-title-text {
  font-size: 15px;
  font-weight: 600;
}

/* alert */
.mp-alert {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.5;
  margin: 0 12px 10px;
  border-radius: 20px;
  overflow: hidden;
}
.mp-alert--info {
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
}
.mp-alert--primary {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.mp-alert--success {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}
.mp-alert--warning {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}
.mp-alert--error {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}
.mp-alert-title {
  font-weight: 500;
}
.mp-alert-desc {
  font-size: 12px;
  margin-top: 2px;
  opacity: 0.8;
}

/* tag selector（竖排，在分组卡片内） */
.mp-tag-sel {
  padding: 12px 16px;
}
.mp-tag-sel__label {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
.mp-tag-sel__content {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 36px;
}
.mp-tag-add {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1.5px dashed var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}

/* textarea */
.mp-textarea-body {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  min-height: 56px;
  line-height: 1.6;
  width: 100%;
}

/* switch */
.mp-switch {
  position: relative;
  width: 48px;
  height: 26px;
  border-radius: 26px;
  background: var(--el-border-color);
  flex-shrink: 0;
  margin-left: auto;
}
.mp-switch-node {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--el-bg-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* stepper */
.mp-stepper {
  display: flex;
  align-items: center;
  margin-left: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}
.mp-stepper-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  cursor: pointer;
  user-select: none;
}
.mp-stepper-val {
  padding: 0 10px;
  font-size: 14px;
  color: var(--el-text-color-primary);
  border-left: 1px solid var(--el-border-color);
  border-right: 1px solid var(--el-border-color);
}

/* radio / checkbox */
.mp-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}
.mp-opt-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.mp-radio-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mp-radio-icon--on {
  border-color: var(--el-color-primary);
}
.mp-radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--el-color-primary);
}
.mp-cb-icon {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 1.5px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mp-cb-icon--on {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
}
.mp-opt-label {
  font-size: 13px;
  color: var(--el-text-color-primary);
}

/* rate */
.mp-rate {
  display: flex;
  align-items: center;
  gap: 4px;
}
.mp-star--on {
  fill: var(--el-color-warning);
  stroke: var(--el-color-warning);
}
.mp-star--off {
  fill: none;
  stroke: var(--el-border-color);
}

/* slider */
.mp-slider-wrap {
  position: relative;
  width: 100%;
  height: 20px;
  display: flex;
  align-items: center;
}
.mp-slider-track {
  position: absolute;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--el-border-color-lighter);
  border-radius: 4px;
}
.mp-slider-fill {
  position: absolute;
  left: 0;
  height: 4px;
  background: var(--el-color-primary);
  border-radius: 4px;
}
.mp-slider-thumb {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--el-bg-color);
  border: 2px solid var(--el-color-primary);
  transform: translateX(-50%);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* upload */
.mp-upload {
  display: flex;
  gap: 8px;
}
.mp-upload-btn {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  border: 1.5px dashed var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  background-color: var(--el-fill-color);
}
.mp-upload-btn:hover {
  background-color: var(--el-fill-color-light);
}

/* rich-text */
.mp-richtext {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  min-height: 48px;
  line-height: 1.6;
  border: 1px dashed var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 8px;
  width: 100%;
  box-sizing: border-box;
}

/* signature - standalone card */
.mp-signature {
  background: var(--el-bg-color);
  border-radius: 20px;
  margin: 0 12px 10px;
  padding: 16px;
}
.mp-signature-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}
.mp-signature-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 120px;
  border: 1px dashed var(--el-border-color-lighter);
  border-radius: 12px;
  background-color: var(--el-fill-color-lighter);
  cursor: pointer;
}
.mp-signature-hint {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}

/* qrcode - standalone card */
.mp-qrcode {
  background: var(--el-bg-color);
  border-radius: 20px;
  margin: 0 12px 10px;
  padding: 16px;
}
.mp-qrcode-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}
.mp-qrcode-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 120px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  background-color: #fff;
}

/* tabs */
.mp-tabs-nav {
  display: flex;
  position: relative;
  border-bottom: 0.5px solid var(--el-border-color-lighter);
}
.mp-tabs-nav--card {
  border-bottom: none;
  margin: 8px;
  background: var(--el-fill-color);
  border-radius: 8px;
  padding: 3px;
}
.mp-tab {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  white-space: nowrap;
}
.mp-tab--active {
  color: var(--el-color-primary);
  font-weight: 600;
}
.mp-tabs-nav--card .mp-tab--active {
  background: var(--el-bg-color);
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.mp-tab-line {
  position: absolute;
  bottom: 0;
  height: 3px;
  background: var(--el-color-primary);
  border-radius: 3px;
  transition:
    left 0.3s,
    width 0.3s;
}

/* steps */
.mp-steps-nav {
  display: flex;
  align-items: flex-start;
  padding: 16px 12px;
  border-bottom: 0.5px solid var(--el-border-color-lighter);
}
.mp-step-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}
.mp-step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}
.mp-step-icon--done,
.mp-step-icon--active {
  background: var(--el-color-primary);
}
.mp-step-icon--wait {
  background: var(--el-border-color-lighter);
}
.mp-step-num {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-bg-color);
}
.mp-step-icon--wait .mp-step-num {
  color: var(--el-text-color-placeholder);
}
.mp-step-title {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  text-align: center;
}
.mp-step-title--active {
  color: var(--el-color-primary);
  font-weight: 500;
}
.mp-step-title--done {
  color: var(--el-text-color-primary);
}
.mp-step-line {
  position: absolute;
  top: 12px;
  left: 50%;
  width: 100%;
  height: 1.5px;
  background: var(--el-border-color-lighter);
}
.mp-step-line--done {
  background: var(--el-color-primary);
}

/* collapse */
.mp-collapse-item {
  border-bottom: 0.5px solid var(--el-border-color-lighter);
}
.mp-collapse-item--last {
  border-bottom: none;
}
.mp-collapse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
}
.mp-collapse-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}
.mp-collapse-arrow {
  transition: transform 0.3s;
  flex-shrink: 0;
  color: var(--el-text-color-placeholder);
}
.mp-collapse-arrow--up {
  transform: rotate(180deg);
}
.mp-collapse-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.mp-collapse-body--open {
  max-height: 2000px;
}

/* sub-table */
.mp-subtable {
  margin: 6px 10px;
  background: var(--el-bg-color);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}
.mp-subtable-header {
  padding: 14px 16px;
  background: var(--el-bg-color);
  border-bottom: 0.5px solid var(--el-border-color-lighter);
}
.mp-subtable-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}
.mp-subtable-list {
  padding: 10px 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mp-subtable-card {
  background: var(--el-bg-color);
  border-radius: 20px;
  overflow: hidden;
  margin: 0 12px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}
.mp-subtable-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 0.5px solid var(--el-border-color-lighter);
}
.mp-subtable-tag {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 2px 8px;
  border-radius: 10px;
}
.mp-subtable-card-body {
  overflow: hidden;
}
.mp-subtable-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 0 12px 12px 12px;
  padding: 11px;
  border: 1.5px solid var(--el-color-primary);
  border-radius: 8px;
  font-size: 13px;
  color: var(--el-color-primary);
  cursor: pointer;
  background: transparent;
}

/* ai-image-ocr */
.mp-ocr-label {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 13px 16px 0;
}
.mp-ocr-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: 6px;
  padding: 2px 7px;
  background: var(--el-color-primary);
  color: var(--el-color-white);
  font-size: 11px;
  font-weight: 600;
  border-radius: 8px;
}
.mp-ocr-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px 16px;
  gap: 8px;
  border: 1.5px dashed var(--el-border-color);
  border-radius: 12px;
  margin: 16px 0;
  background: var(--el-fill-color-light);
  width: 100%;
}
.mp-ocr-upload-icon {
  color: var(--el-text-color-placeholder);
}
.mp-ocr-upload-text {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}
.mp-ocr-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}
.mp-ocr-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 8px;
}
.mp-ocr-tag--primary {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.mp-ocr-tag--info {
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
}
</style>
