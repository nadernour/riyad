/**
 * @jest-environment node
 */
import { PALETTES, type Colors } from './index';

jest.mock('@/db/userDb', () => ({ userDb: () => null }));

// WCAG 2's contrast ratio between two colours written #RRGGBB.
function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((at) => {
    const c = parseInt(hex.slice(at, at + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

const TEXT: (keyof Colors)[] = ['text', 'muted', 'accent', 'prophet', 'speech'];

test.each(
  Object.entries(PALETTES).flatMap(([name, modes]) => Object.entries(modes).map(([mode, c]) => [name, mode, c])),
)(
  'every text colour of the %s palette, %s, is readable on its background and behind a highlight',
  (_name, _mode, colors) => {
    const c = colors as Colors;
    for (const key of TEXT) expect(contrast(c[key], c.background)).toBeGreaterThanOrEqual(4.5);
    // The highlight is behind the hadith text only, where the Prophet's words are bold.
    for (const key of ['text', 'speech'] as const) expect(contrast(c[key], c.highlight)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c.prophet, c.highlight)).toBeGreaterThanOrEqual(4.3);
  },
);
