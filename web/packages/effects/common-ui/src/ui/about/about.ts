import type { Component } from 'vue';

interface AboutLabels {
  author?: string;
  basicInfo?: string;
  buildTime?: string;
  devDependencies?: string;
  docUrl?: string;
  github?: string;
  homepage?: string;
  license?: string;
  previewUrl?: string;
  productionDependencies?: string;
  version?: string;
  viewDetails?: string;
}

interface AboutProps {
  description?: string;
  labels?: AboutLabels;
  name?: string;
  title?: string;
}

interface DescriptionItem {
  content: Component | string;
  title: string;
}

export type { AboutLabels, AboutProps, DescriptionItem };
