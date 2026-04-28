import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
  setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'light',
  toggleTheme: () => {},
  setTheme: () => {},
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme] = useState<Theme>('light')

  useEffect(() => {
    // Always force light mode — remove any previously stored dark class
    document.documentElement.classList.remove('dark')
    try { localStorage.removeItem('rh_theme') } catch {}
  }, [])

  const setTheme = (_t: Theme) => {} // no-op: light mode locked
  const toggleTheme = () => {}       // no-op: light mode locked

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
