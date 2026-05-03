/**
 * 表单编辑器公共组件
 * 可用于：表单管理器、工作流设计预览编辑
 */

export { default as BasicInfoEditor } from './BasicInfoEditor.vue';
export type { BasicFormData } from './BasicInfoEditor.vue';

export { default as DesignEditorPanel } from './DesignEditorPanel.vue';
export type { DesignData, DesignType } from './DesignEditorPanel.vue';

export { default as FormEditorContent } from './FormEditorContent.vue';
export type { FormEditorData, BasicFormData as FormBasicData } from './FormEditorContent.vue';

export { default as AppDesignPanel } from './AppDesignPanel.vue';
export type { AppDesignData } from './AppDesignPanel.vue';

export { default as AppSettingsPanel } from './AppSettingsPanel.vue';
export type { AppSettingsData } from './AppSettingsPanel.vue';

export { default as DashboardBasicInfoConfirmPanel } from './DashboardBasicInfoConfirmPanel.vue';
export type { DashboardBasicInfoData } from './DashboardBasicInfoConfirmPanel.vue';

export { default as DashboardDesignConfirmPanel } from './DashboardDesignConfirmPanel.vue';
export type { DashboardDesignData } from './DashboardDesignConfirmPanel.vue';

export { default as PageBasicInfoEditor } from './PageBasicInfoEditor.vue';
export type { PageBasicInfo } from './PageBasicInfoEditor.vue';

export { default as PagePublishInfoEditor } from './PagePublishInfoEditor.vue';
export type { PagePublishInfo } from './PagePublishInfoEditor.vue';

export { default as PageEditorContent } from './PageEditorContent.vue';
export type { PageEditorData } from './PageEditorContent.vue';

export { default as DashboardPublishConfirmPanel } from './DashboardPublishConfirmPanel.vue';
export type { DashboardPublishData } from './DashboardPublishConfirmPanel.vue';

export { default as SystemSummaryConfirmPanel } from './SystemSummaryConfirmPanel.vue';
export type { SystemSummaryData } from './SystemSummaryConfirmPanel.vue';
