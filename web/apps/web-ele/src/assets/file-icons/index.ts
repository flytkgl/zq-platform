import audioIcon from './audio.svg';
import codeIcon from './code.svg';
import excelIcon from './excel.svg';
import imageIcon from './image.svg';
import pdfIcon from './pdf.svg';
import pptIcon from './ppt.svg';
import txtIcon from './txt.svg';
import unknownIcon from './unknown.svg';
import videoIcon from './video.svg';
import wordIcon from './word.svg';
import zipIcon from './zip.svg';

const EXT_MAP: Record<string, string> = {
  // PDF
  pdf: pdfIcon,
  // Word
  doc: wordIcon,
  docx: wordIcon,
  // Excel
  xls: excelIcon,
  xlsx: excelIcon,
  csv: excelIcon,
  // PPT
  ppt: pptIcon,
  pptx: pptIcon,
  // 图片
  jpg: imageIcon,
  jpeg: imageIcon,
  png: imageIcon,
  gif: imageIcon,
  bmp: imageIcon,
  svg: imageIcon,
  webp: imageIcon,
  ico: imageIcon,
  tiff: imageIcon,
  // 视频
  mp4: videoIcon,
  avi: videoIcon,
  mov: videoIcon,
  mkv: videoIcon,
  webm: videoIcon,
  flv: videoIcon,
  wmv: videoIcon,
  // 音频
  mp3: audioIcon,
  wav: audioIcon,
  ogg: audioIcon,
  flac: audioIcon,
  aac: audioIcon,
  wma: audioIcon,
  // 压缩
  zip: zipIcon,
  rar: zipIcon,
  '7z': zipIcon,
  tar: zipIcon,
  gz: zipIcon,
  bz2: zipIcon,
  // 代码
  js: codeIcon,
  ts: codeIcon,
  jsx: codeIcon,
  tsx: codeIcon,
  vue: codeIcon,
  svelte: codeIcon,
  py: codeIcon,
  java: codeIcon,
  c: codeIcon,
  cpp: codeIcon,
  h: codeIcon,
  hpp: codeIcon,
  cs: codeIcon,
  go: codeIcon,
  rs: codeIcon,
  rb: codeIcon,
  php: codeIcon,
  swift: codeIcon,
  kt: codeIcon,
  scala: codeIcon,
  lua: codeIcon,
  r: codeIcon,
  pl: codeIcon,
  sh: codeIcon,
  bash: codeIcon,
  zsh: codeIcon,
  bat: codeIcon,
  cmd: codeIcon,
  ps1: codeIcon,
  html: codeIcon,
  htm: codeIcon,
  css: codeIcon,
  scss: codeIcon,
  sass: codeIcon,
  less: codeIcon,
  sql: codeIcon,
  graphql: codeIcon,
  proto: codeIcon,
  dockerfile: codeIcon,
  makefile: codeIcon,
  cmake: codeIcon,
  // 纯文本
  txt: txtIcon,
  md: txtIcon,
  log: txtIcon,
  json: txtIcon,
  xml: txtIcon,
  yaml: txtIcon,
  yml: txtIcon,
  toml: txtIcon,
  ini: txtIcon,
  conf: txtIcon,
  cfg: txtIcon,
  env: txtIcon,
};

/**
 * 根据文件扩展名获取对应的文件类型图标
 * @param ext 文件扩展名（带或不带点号）
 * @returns SVG 图标路径
 */
export function getFileTypeIcon(ext?: null | string): string {
  if (!ext) return unknownIcon;
  const normalized = ext.toLowerCase().replace(/^\./, '');
  return EXT_MAP[normalized] || unknownIcon;
}

export {
  audioIcon,
  codeIcon,
  excelIcon,
  imageIcon,
  pdfIcon,
  pptIcon,
  txtIcon,
  unknownIcon,
  videoIcon,
  wordIcon,
  zipIcon,
};
