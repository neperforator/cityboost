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
          50: '#E8F1ED',
          100: '#C9E0D7',
          200: '#9CC7B8',
          300: '#6BA893',
          400: '#3D8871',
          500: '#0E5A4A',
          600: '#0B4B3E',
          700: '#093D33',
          800: '#072F27',
          900: '#05211C',
        },
        // Safety orange — used only for action and attention
        accent: {
          50: '#FDECE6',
          100: '#FAD3C5',
          200: '#F4A88F',
          300: '#EE7D5B',
          400: '#E95F39',
          500: '#E4572E',
          600: '#C4431F',
          700: '#A03519',
          800: '#7C2913',
          900: '#5C1E0E',
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
          DEFAULT: '#EEF0EC',
          dark: '#101614',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F6F7F4',
          dark: '#161D1A',
          'dark-muted': '#1D2521',
        },
        ink: {
          DEFAULT: '#16201C',
          soft: '#4A554F',
          dark: '#E8ECE6',
          'dark-soft': '#A7B2AB',
        },
        line: {
          DEFAULT: '#D7DCD5',
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
        panel: '4px 4px 0 0 rgb(22 32 28 / 0.08)',
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
