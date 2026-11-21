/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Municipal pine — the service-line colour
        primary: {
          50: '#EDF4F1',
          100: '#D8E7E1',
          200: '#B2D1C5',
          300: '#7FB29F',
          400: '#4A8C77',
          500: '#0E5A4A',
          600: '#0B4B3E',
          700: '#093D33',
          800: '#072F27',
          900: '#05211C',
        },
        // Muted terracotta — used only for action and attention
        accent: {
          50: '#FCF0EA',
          100: '#F7DCCF',
          200: '#EDB9A2',
          300: '#DE9172',
          400: '#CF6B47',
          500: '#C2512C',
          600: '#A84322',
          700: '#8A361B',
          800: '#6C2A15',
          900: '#512010',
        },
        // Map blue — for location and secondary information
        map: {
          50: '#EAF2F5',
          100: '#D2E2E9',
          200: '#A9C6D3',
          300: '#7FA9BB',
          400: '#4F839A',
          500: '#2E6F8E',
          600: '#245A74',
          700: '#1C475C',
          800: '#153645',
          900: '#0F2732',
        },
        canvas: {
          DEFAULT: '#F5F6F8',
          dark: '#101614',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F2F4F6',
          dark: '#161D1A',
          'dark-muted': '#1D2521',
        },
        ink: {
          DEFAULT: '#1B2027',
          soft: '#5A6472',
          dark: '#E8ECE6',
          'dark-soft': '#A7B2AB',
        },
        line: {
          DEFAULT: '#E2E6EA',
          dark: '#2A342F',
        },
      },
      fontFamily: {
        sans: ['Onest', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        display: ['Unbounded', 'Onest', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '2px',
        DEFAULT: '4px',
        md: '6px',
        lg: '8px',
        xl: '12px',
      },
      boxShadow: {
        panel: '4px 4px 0 0 rgb(27 32 39 / 0.08)',
        none: 'none',
      },
      keyframes: {
        lineIn: {
          '0%': { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
      },
      animation: {
        'line-in': 'lineIn 0.5s cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
    },
  },
  plugins: [],
}
