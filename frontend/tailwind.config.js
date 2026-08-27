/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#dde7ff',
          200: '#c2d3ff',
          300: '#9bb5ff',
          400: '#7090ff',
          500: '#4c6ef5',
          600: '#3a54e8',
          700: '#2f42cd',
          800: '#2a39a7',
          900: '#273584',
        },
        accent: {
          50: '#fdf2ff',
          100: '#fae5ff',
          200: '#f5c9ff',
          300: '#ed9dff',
          400: '#e062ff',
          500: '#cc33f0',
          600: '#b018d3',
          700: '#9313aa',
          800: '#7a128b',
          900: '#651471',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          from: { boxShadow: '0 0 5px #4c6ef5, 0 0 10px #4c6ef5' },
          to: { boxShadow: '0 0 10px #4c6ef5, 0 0 30px #4c6ef5, 0 0 60px #4c6ef5' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
