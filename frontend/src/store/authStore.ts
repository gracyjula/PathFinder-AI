import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/lib/api'
import type { User, LearnerProfile, TokenResponse } from '@/types'

interface AuthState {
  user: User | null
  profile: LearnerProfile | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; username: string; password: string; full_name?: string }) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
  fetchProfile: () => Promise<void>
  setProfile: (profile: LearnerProfile) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await api.post<TokenResponse>('/auth/login', { email, password })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          await get().fetchMe()
          set({ isAuthenticated: true })
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (registerData) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/register', registerData)
          await get().login(registerData.email, registerData.password)
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, profile: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        const { data } = await api.get<User>('/auth/me')
        set({ user: data, isAuthenticated: true })
        // Try to fetch profile
        try {
          await get().fetchProfile()
        } catch {
          // Profile might not exist yet
        }
      },

      fetchProfile: async () => {
        const { data } = await api.get<LearnerProfile>('/profile')
        set({ profile: data })
      },

      setProfile: (profile) => set({ profile }),
    }),
    {
      name: 'neuralearn-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
