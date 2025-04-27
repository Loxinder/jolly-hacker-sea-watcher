/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-geist-sans)'],
        mono: ['var(--font-geist-mono)'],
      },
      textColor: {
        foreground: 'var(--foreground)',
        'button-text': 'var(--button-text)',
        label: 'var(--label-color)',
      },
      backgroundColor: {
        'button-bg': 'var(--button-bg)',
        'button-hover-bg': 'var(--button-hover-bg)',
      },
    },
  },
  plugins: [],
}