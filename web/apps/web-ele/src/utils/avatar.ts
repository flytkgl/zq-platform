/**
 * 头像生成工具函数
 */

/**
 * 判断是否是汉字
 */
function isChinese(char: string): boolean {
  const code = char.charCodeAt(0);
  return code >= 0x4E_00 && code <= 0x9F_FF;
}

/**
 * 从名字生成头像文本
 * - 汉字：显示第一个字
 * - 字母：显示前两个字母
 * - 其他：显示第一个字符
 */
export function generateAvatarText(name?: string): string {
  if (!name) {
    return '?';
  }

  const trimmedName = name.trim();
  if (trimmedName.length === 0) {
    return '?';
  }

  const firstChar = trimmedName.charAt(0);

  // 如果第一个字是汉字
  if (isChinese(firstChar)) {
    return firstChar;
  }

  // 如果是字母，显示前两个字母
  if (/[a-z]/i.test(firstChar)) {
    let result = '';
    for (let i = 0; i < trimmedName.length && result.length < 2; i++) {
      const char = trimmedName.charAt(i);
      if (/[a-z]/i.test(char)) {
        result += char.toUpperCase();
      }
    }
    return result || firstChar.toUpperCase();
  }

  // 其他情况返回第一个字符
  return firstChar;
}

/**
 * 根据名字生成稳定的渐变颜色配置
 * 使用哈希算法确保相同的名字生成相同的颜色
 */
export function generateAvatarGradient(name?: string): string {
  if (!name) {
    return 'linear-gradient(135deg, #8b9dff 0%, #a78bfa 100%)';
  }

  // 预设的美观渐变颜色 - 中等饱和度版本
  const gradients: string[] = [
    'linear-gradient(135deg, #8b9dff 0%, #a78bfa 100%)', // 紫蓝渐变
    'linear-gradient(135deg, #f59dba 0%, #fa709a 100%)', // 粉红渐变
    'linear-gradient(135deg, #60c5ff 0%, #7dd3fc 100%)', // 青蓝渐变
    'linear-gradient(135deg, #6ee7b7 0%, #5eead4 100%)', // 绿松渐变
    'linear-gradient(135deg, #fb923c 0%, #fbbf24 100%)', // 橙金渐变
    'linear-gradient(135deg, #a78bfa 0%, #f472b6 100%)', // 紫粉渐变
    'linear-gradient(135deg, #f472b6 0%, #fb923c 100%)', // 粉橙渐变
    'linear-gradient(135deg, #818cf8 0%, #c084fc 100%)', // 蓝紫渐变
    'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)', // 天蓝渐变
    'linear-gradient(135deg, #34d399 0%, #a3e635 100%)', // 绿黄渐变
    'linear-gradient(135deg, #fb7185 0%, #fda4af 100%)', // 玫红渐变
    'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)', // 青色渐变
    'linear-gradient(135deg, #d946ef 0%, #f0abfc 100%)', // 品红渐变
    'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)', // 琥珀渐变
    'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)', // 紫色渐变
    'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)', // 蔚蓝渐变
    'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)', // 粉色渐变
    'linear-gradient(135deg, #10b981 0%, #34d399 100%)', // 翠绿渐变
    'linear-gradient(135deg, #a855f7 0%, #c084fc 100%)', // 紫罗兰渐变
    'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)', // 蓝色渐变
  ];

  // 简单的哈希函数：计算字符串的哈希值
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    const char = name.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // 转换为 32 位整数
  }

  // 使用哈希值选择颜色
  const index = Math.abs(hash) % gradients.length;
  return gradients[index]!;
}

/**
 * 根据名字生成稳定的背景颜色（保留用于兼容）
 */
export function generateAvatarColor(name?: string): string {
  const gradient = generateAvatarGradient(name);
  // 从渐变中提取主要颜色用于兼容
  if (gradient.includes('#667eea')) return '#667eea';
  if (gradient.includes('#f093fb')) return '#f093fb';
  if (gradient.includes('#4facfe')) return '#4facfe';
  return '#667eea'; // 默认
}

/**
 * 生成头像的完整配置对象
 */
export interface AvatarConfig {
  text: string;
  backgroundColor: string;
  gradient: string;
  color?: string;
}

/**
 * 根据名字生成完整的头像配置
 */
export function generateAvatarConfig(name?: string): AvatarConfig {
  return {
    text: generateAvatarText(name),
    backgroundColor: generateAvatarColor(name),
    gradient: generateAvatarGradient(name),
    color: '#ffffff', // 文字颜色总是白色
  };
}
