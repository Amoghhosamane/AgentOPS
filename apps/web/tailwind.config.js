/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          light: '#F8FAFC',
          dark: '#090E1A',
        },
        surface: {
          light: '#FFFFFF',
          dark: '#111827',
          elevated: '#1F2937',
        },
        primary: {
          light: '#2563EB',
          dark: '#60A5FA',
        },
      },
    },
  },
  plugins: [],
};
