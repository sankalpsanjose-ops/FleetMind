/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg:      '#000510',
          panel:   '#020c1b',
          border:  'rgba(0,255,180,0.25)',
          cyan:    '#00ffb4',
          blue:    '#00c8ff',
          red:     '#ff3333',
          orange:  '#ff8c00',
          dim:     'rgba(0,255,180,0.5)',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'cyan-glow':   '0 0 12px rgba(0,255,180,0.5)',
        'red-glow':    '0 0 12px rgba(255,51,51,0.6)',
        'blue-glow':   '0 0 12px rgba(0,200,255,0.5)',
      },
    },
  },
  plugins: [],
}
