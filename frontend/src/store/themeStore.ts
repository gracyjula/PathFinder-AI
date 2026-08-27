import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
  setTheme: (t: Theme) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark',
      toggleTheme: () =>
        set((s) => {
          const next = s.theme === 'dark' ? 'light' : 'dark'
          document.documentElement.setAttribute('data-theme', next)
          return { theme: next }
        }),
      setTheme: (t) => {
        document.documentElement.setAttribute('data-theme', t)
        set({ theme: t })
      },
    }),
    { name: 'neuralearn-theme' }
  )
)

/** Call once on app boot to sync HTML attribute with persisted value */
export function initTheme() {
  const raw = localStorage.getItem('neuralearn-theme')
  const theme: Theme = raw ? (JSON.parse(raw)?.state?.theme ?? 'dark') : 'dark'
  document.documentElement.setAttribute('data-theme', theme)
}
