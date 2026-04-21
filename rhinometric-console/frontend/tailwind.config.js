/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ── Brand ─────────────────────────────────────────────────
        primary: {
          DEFAULT: 'var(--c-primary)',
          dark:    'var(--c-primary-dark)',
          light:   'var(--c-primary-light)',
        },
        secondary: {
          DEFAULT: '#14b8a6',
          dark:    '#0d9488',
          light:   '#2dd4bf',
        },

        // ── App surfaces (light/dark via CSS vars) ─────────────────
        background:      'var(--c-bg)',
        surface:         'var(--c-surface)',
        'surface-dark':  'var(--c-surface-dark)',
        'surface-light': 'var(--c-surface-light)',
        border:          'var(--c-border)',

        // ── Typography ────────────────────────────────────────────
        text: {
          primary:   'var(--c-text-primary)',
          secondary: 'var(--c-text-secondary)',
          muted:     'var(--c-text-muted)',
        },

        // ── Semantic status ───────────────────────────────────────
        error:    'var(--c-critical)',
        success:  'var(--c-success)',
        warning:  'var(--c-warning)',
        critical: 'var(--c-critical)',
        info:     'var(--c-info)',

        // ── Sidebar tokens (always dark) ──────────────────────────
        sidebar: {
          bg:          'var(--c-sidebar-bg)',
          border:      'var(--c-sidebar-border)',
          text:        'var(--c-sidebar-text)',
          'text-hover':'var(--c-sidebar-text-hover)',
          section:     'var(--c-sidebar-section)',
          'active-bg': 'var(--c-sidebar-active-bg)',
          'active-text':'var(--c-sidebar-active-text)',
          'hover-bg':  'var(--c-sidebar-hover-bg)',
        },
      },

      // ── Shadows via CSS vars ──────────────────────────────────
      boxShadow: {
        sm:  'var(--shadow-sm)',
        md:  'var(--shadow-md)',
        lg:  'var(--shadow-lg)',
        card:'var(--shadow-md)',
      },

      // ── Border radius via CSS vars ────────────────────────────
      borderRadius: {
        sm:  'var(--radius-sm)',
        md:  'var(--radius-md)',
        lg:  'var(--radius-lg)',
        xl:  'var(--radius-xl)',
      },

      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-slow':'pulse 3s ease-in-out infinite',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
