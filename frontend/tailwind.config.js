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
        // Warm accent for CTAs and highlights
        accent: {
          50: '#FEF7EE',
          100: '#FDEDD8',
          200: '#FBD7AE',
          300: '#F8B97A',
          400: '#F59E4D',
          500: '#E8822A',
          600: '#D4691A',
          700: '#B05115',
          800: '#8D4019',
          900: '#733617',
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
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'card-hover': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04)',
        'dropdown': '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        'modal': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.05)',
        'sidebar': '4px 0 6px -1px rgb(0 0 0 / 0.05)',
        'nav': '0 1px 3px 0 rgb(0 0 0 / 0.04)',
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
