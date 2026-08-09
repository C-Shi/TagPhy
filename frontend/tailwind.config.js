/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--color-canvas)',
        panel: 'var(--color-panel)',
        surface: 'var(--color-surface)',
        header: {
          DEFAULT: 'var(--color-header)',
          muted: 'var(--color-header-muted)',
        },
        ink: {
          DEFAULT: 'var(--color-ink)',
          muted: 'var(--color-ink-muted)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          soft: 'var(--color-accent-soft)',
        },
        on: {
          accent: 'var(--color-on-accent)',
          chip: 'var(--color-chip-text)',
        },
        line: 'var(--color-line)',
        label: {
          yellow: 'var(--color-label-yellow)',
          orange: 'var(--color-label-orange)',
          blue: 'var(--color-label-blue)',
          pink: 'var(--color-label-pink)',
        },
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      screens: {
        library: '900px',
      },
    },
  },
  plugins: [],
}
