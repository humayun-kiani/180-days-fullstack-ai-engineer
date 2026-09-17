export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Safe area for notched phones
      padding: {
        'safe-bottom': 'env(safe-area-inset-bottom)',
      },
      minHeight: {
        'touch': '44px',   // WCAG minimum touch target
      },
      minWidth: {
        'touch': '44px',
      }
    }
  },
  plugins: []
}