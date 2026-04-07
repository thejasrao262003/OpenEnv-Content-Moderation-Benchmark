/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'monospace'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        bg:        '#080810',
        surface:   '#0f0f1a',
        surface2:  '#151525',
        dim:       '#1f1f35',
        dimBright: '#2a2a45',
        muted:     '#5a5f7a',
        faint:     '#3a3f5a',
        body:      '#dde1f0',
        amber:     '#f0a500',
      },
      keyframes: {
        stepReveal: {
          from: { opacity: '0', transform: 'translateX(-10px)' },
          to:   { opacity: '1', transform: 'translateX(0)' },
        },
        fillBar: {
          from: { transform: 'scaleX(0)' },
          to:   { transform: 'scaleX(1)' },
        },
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        scanPulse: {
          '0%,100%': { opacity: '0.4' },
          '50%':     { opacity: '1' },
        },
      },
      animation: {
        stepReveal: 'stepReveal 0.35s ease forwards',
        fillBar:    'fillBar 0.9s cubic-bezier(0.16,1,0.3,1) forwards',
        fadeUp:     'fadeUp 0.45s ease forwards',
        scanPulse:  'scanPulse 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
