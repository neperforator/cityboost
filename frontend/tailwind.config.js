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
        // Civic Navy — professional, trustworthy palette
        // Distinctive from generic Tailwind indigo
        primary: {
          50: '#EBF4FF',
          100: '#D6E8FF',
          200: '#A8CCF5',
          300: '#7AACE8',
          400: '#4D8EDB',
          500: '#2B6CB0',
          600: '#1E4D8C',
          700: '#153A6B',
          800: '#0F2B50',
          900: '#091B35',
        },
        // Emerald accent for CTAs and highlights ("service green")
        accent: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
        // Surface colors for cards, modals, etc.
        surface: {
          DEFAULT: '#FFFFFF',
          secondary: '#F8FAFC',
          muted: '#F1F5F9',
          'dark': '#1A202C',
          'dark-secondary': '#1E293B',
          'dark-muted': '#0F172A',
        },
        // Page canvas — cool, light blue-gray (dark: near-black navy)
        canvas: {
          DEFAULT: '#F6F8FB',
          dark: '#0B1220',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Manrope', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.08)',
        'card-hover': '0 8px 24px -6px rgb(16 24 40 / 0.12), 0 2px 6px -2px rgb(16 24 40 / 0.06)',
        'dropdown': '0 8px 16px -4px rgb(16 24 40 / 0.1), 0 2px 4px -2px rgb(16 24 40 / 0.05)',
        'modal': '0 24px 48px -12px rgb(16 24 40 / 0.18), 0 8px 16px -8px rgb(16 24 40 / 0.1)',
        'sidebar': '4px 0 6px -1px rgb(0 0 0 / 0.05)',
        'nav': '0 1px 3px 0 rgb(0 0 0 / 0.04)',
        'emerald-glow': '0 8px 20px -6px rgb(16 185 129 / 0.4)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
