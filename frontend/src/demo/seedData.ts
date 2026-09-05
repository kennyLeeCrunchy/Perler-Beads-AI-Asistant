import type { BeadColor, Work } from '../types';

// 仅用于首次打开产品时填充示例作品；真实生成的作品会写入浏览器存储。

export const palette: BeadColor[] = [
  { brand: 'Mard', code: 'M01', name: '奶油白', hex: '#F7EEDC', count: 118, remaining: 62 },
  { brand: 'Mard', code: 'M23', name: '焦糖棕', hex: '#9B5B36', count: 214, remaining: 108 },
  { brand: 'Mard', code: 'M27', name: '栗子棕', hex: '#5D382B', count: 168, remaining: 74 },
  { brand: 'Mard', code: 'M34', name: '蜜橘', hex: '#E8874A', count: 236, remaining: 125 },
  { brand: 'Mard', code: 'M44', name: '暖黄', hex: '#F4C65D', count: 92, remaining: 46 },
  { brand: 'Mard', code: 'M71', name: '苔藓绿', hex: '#849B70', count: 67, remaining: 31 },
  { brand: 'Artkal', code: 'A06', name: '雾蓝', hex: '#75AFC0', count: 184, remaining: 80 },
  { brand: 'Artkal', code: 'A18', name: '深海蓝', hex: '#376C84', count: 126, remaining: 55 },
  { brand: 'Artkal', code: 'A33', name: '珊瑚粉', hex: '#D9827A', count: 109, remaining: 51 },
  { brand: 'Artkal', code: 'A42', name: '炭黑', hex: '#30353A', count: 74, remaining: 29 },
];

const baseTime = '2026-07-19T10:30:00.000Z';

export const seedWorks: Work[] = [
  { id: 'shiba', name: '柴犬挂饰', size: '52×52', board: '单板', brand: 'Mard', colors: 14, beads: 963, status: '草稿', createdAt: baseTime, updatedAt: baseTime, progress: 46, palette: palette.slice(0, 6), grid: [], motif: 'dog' },
  { id: 'girl', name: '像素风女生头像', size: '78×78', board: '2×2 拼板', brand: 'Artkal', colors: 26, beads: 2841, status: '已完成', createdAt: baseTime, updatedAt: '2026-07-18T08:20:00.000Z', progress: 100, palette: palette.slice(6), grid: [], motif: 'girl' },
  { id: 'whale', name: '蓝色小鲸鱼', size: '52×52', board: '单板', brand: 'Artkal', colors: 9, beads: 712, status: '已完成', createdAt: baseTime, updatedAt: '2026-07-17T12:00:00.000Z', progress: 100, palette: palette.slice(6), grid: [], motif: 'whale' },
  { id: 'flower', name: '花朵图案', size: '52×52', board: '单板', brand: 'Mard', colors: 11, beads: 805, status: '草稿', createdAt: baseTime, updatedAt: '2026-07-16T09:10:00.000Z', progress: 28, palette: palette.slice(0, 6), grid: [], motif: 'flower' },
];

export const getWork = (id?: string) => seedWorks.find((work) => work.id === id) ?? seedWorks[0];
