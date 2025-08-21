import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('access_token'))

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api'

  useEffect(() => {
    // Check if user is logged in on app start
    if (token) {
      fetchProfile()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setProfile(data.data)
          // Get user info from token payload (simplified)
          const tokenPayload = JSON.parse(atob(token.split('.')[1]))
          setUser({
            id: tokenPayload.user_id,
            email: tokenPayload.email,
            name: tokenPayload.name
          })
        } else {
          throw new Error(data.error)
        }
      } else {
        throw new Error('Failed to fetch profile')
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        const { access_token } = data.data.tokens
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', data.data.tokens.refresh_token)
        setToken(access_token)
        setUser(data.data.user)
        setProfile(data.data.profile)
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Login failed' }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: 'Network error' }
    }
  }

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      })

      const data = await response.json()

      if (response.ok && data.success) {
        const { access_token } = data.data.tokens
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', data.data.tokens.refresh_token)
        setToken(access_token)
        setUser(data.data.user)
        setProfile(data.data.profile)
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Registration failed' }
      }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, error: 'Network error' }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setToken(null)
    setUser(null)
    setProfile(null)
  }

  const updateProfile = async (profileData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setProfile(data.data)
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Profile update failed' }
      }
    } catch (error) {
      console.error('Profile update error:', error)
      return { success: false, error: 'Network error' }
    }
  }

  const updateLocation = async (locationData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile/location`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(locationData)
      })

      const data = await response.json()

      if (response.ok && data.success) {
        return { success: true, data: data.data }
      } else {
        return { success: false, error: data.error || 'Location update failed' }
      }
    } catch (error) {
      console.error('Location update error:', error)
      return { success: false, error: 'Network error' }
    }
  }

  const value = {
    user,
    profile,
    loading,
    isAuthenticated: !!token,
    login,
    register,
    logout,
    updateProfile,
    updateLocation,
    fetchProfile
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

