import React, { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

const LocationContext = createContext()

export const useLocation = () => {
  const context = useContext(LocationContext)
  if (!context) {
    throw new Error('useLocation must be used within a LocationProvider')
  }
  return context
}

export const LocationProvider = ({ children }) => {
  const { updateLocation, isAuthenticated } = useAuth()
  const [currentLocation, setCurrentLocation] = useState(null)
  const [watchId, setWatchId] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [isTracking, setIsTracking] = useState(false)
  const [tripId, setTripId] = useState(null)
  const [lastNotification, setLastNotification] = useState(null)

  // Start location tracking
  const startTracking = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser')
      return false
    }

    if (isTracking) {
      return true
    }

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000 // 1 minute
    }

    const handleSuccess = async (position) => {
      const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        speed: position.coords.speed,
        heading: position.coords.heading,
        trip_id: tripId
      }

      setCurrentLocation(locationData)
      setLocationError(null)

      // Send location to backend if authenticated
      if (isAuthenticated) {
        try {
          const result = await updateLocation(locationData)
          if (result.success && result.data.notification_sent) {
            setLastNotification(result.data.recommended_station)
            // Show notification to user
            if ('Notification' in window && Notification.permission === 'granted') {
              const station = result.data.recommended_station
              new Notification('⛽ Posto mais barato encontrado!', {
                body: `${station.name} - R$ ${station.fuel_price?.price?.toFixed(2)}/L`,
                icon: '/favicon.ico'
              })
            }
          }
        } catch (error) {
          console.error('Error updating location:', error)
        }
      }
    }

    const handleError = (error) => {
      let errorMessage = 'Unknown location error'
      
      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorMessage = 'Location access denied by user'
          break
        case error.POSITION_UNAVAILABLE:
          errorMessage = 'Location information unavailable'
          break
        case error.TIMEOUT:
          errorMessage = 'Location request timed out'
          break
      }
      
      setLocationError(errorMessage)
      console.error('Location error:', errorMessage)
    }

    const id = navigator.geolocation.watchPosition(
      handleSuccess,
      handleError,
      options
    )

    setWatchId(id)
    setIsTracking(true)
    return true
  }

  // Stop location tracking
  const stopTracking = () => {
    if (watchId) {
      navigator.geolocation.clearWatch(watchId)
      setWatchId(null)
    }
    setIsTracking(false)
    setTripId(null)
  }

  // Start a new trip
  const startTrip = () => {
    const newTripId = `trip_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setTripId(newTripId)
    
    if (!isTracking) {
      startTracking()
    }
    
    return newTripId
  }

  // Stop current trip
  const stopTrip = () => {
    setTripId(null)
    stopTracking()
  }

  // Get current position once
  const getCurrentPosition = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const locationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            speed: position.coords.speed,
            heading: position.coords.heading
          }
          resolve(locationData)
        },
        (error) => {
          reject(error)
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      )
    })
  }

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    }
    return false
  }

  // Calculate distance between two points
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371 // Radius of the Earth in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    const distance = R * c // Distance in kilometers
    return distance
  }

  // Auto-start tracking when authenticated
  useEffect(() => {
    if (isAuthenticated && !isTracking) {
      // Request notification permission
      requestNotificationPermission()
      
      // Auto-start tracking after a short delay
      const timer = setTimeout(() => {
        startTracking()
      }, 2000)

      return () => clearTimeout(timer)
    }
  }, [isAuthenticated])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchId) {
        navigator.geolocation.clearWatch(watchId)
      }
    }
  }, [watchId])

  const value = {
    currentLocation,
    locationError,
    isTracking,
    tripId,
    lastNotification,
    startTracking,
    stopTracking,
    startTrip,
    stopTrip,
    getCurrentPosition,
    requestNotificationPermission,
    calculateDistance
  }

  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  )
}

