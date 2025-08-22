import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  MapPin, 
  Fuel, 
  Bell, 
  TrendingDown, 
  Navigation as NavigationIcon,
  Clock,
  DollarSign,
  AlertCircle,
  CheckCircle,
  Play,
  Square
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useLocation } from '../contexts/LocationContext'
import { formatDistanceToNow } from 'date-fns'
import ptBR from 'date-fns/locale/pt-BR'
import { API_BASE_URL } from '../config'

const Dashboard = () => {
  const { user, profile } = useAuth()
  const { 
    currentLocation, 
    isTracking, 
    startTracking, 
    stopTracking, 
    startTrip, 
    stopTrip, 
    tripId,
    lastNotification,
    locationError
  } = useLocation()
  
  const [nearbyStations, setNearbyStations] = useState([])
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)

  // Fetch nearby stations when location changes
  useEffect(() => {
    if (currentLocation && isTracking) {
      fetchNearbyStations()
    }
  }, [currentLocation])

  // Fetch notifications on component mount
  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNearbyStations = async () => {
    if (!currentLocation) return

    try {
      const response = await fetch(
        `${API_BASE_URL}/gas-stations/nearby?latitude=${currentLocation.latitude}&longitude=${currentLocation.longitude}&radius_km=10&limit=5`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setNearbyStations(data.data.stations)
        }
      }
    } catch (error) {
      console.error('Error fetching nearby stations:', error)
    }
  }

  const fetchNotifications = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile/notifications?per_page=5`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setNotifications(data.data.notifications)
        }
      }
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
  }

  const handleStartTrip = () => {
    const newTripId = startTrip()
    console.log('Trip started:', newTripId)
  }

  const handleStopTrip = () => {
    stopTrip()
    console.log('Trip stopped')
  }

  const getFuelTypeDisplay = (fuelType) => {
    const types = {
      'gasoline': 'Gasolina',
      'ethanol': 'Etanol',
      'diesel': 'Diesel',
      'diesel_s10': 'Diesel S10',
      'gnv': 'GNV'
    }
    return types[fuelType] || fuelType
  }

  return (
    <div className="container mx-auto px-4 py-6 pb-20 md:pb-6">
      {/* Welcome Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Olá, {user?.name?.split(' ')[0]}! 👋
        </h1>
        <p className="text-gray-600 mt-1">
          Acompanhe sua economia e encontre os melhores preços
        </p>
      </div>

      {/* Location Error Alert */}
      {locationError && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {locationError}. Para receber notificações automáticas, permita o acesso à localização.
          </AlertDescription>
        </Alert>
      )}

      {/* GPS Status and Trip Control */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <MapPin className="h-5 w-5 mr-2" />
              Status GPS
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  isTracking ? 'bg-green-500' : 'bg-gray-400'
                }`}></div>
                <span className="font-medium">
                  {isTracking ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <Button
                variant={isTracking ? "destructive" : "default"}
                size="sm"
                onClick={isTracking ? stopTracking : startTracking}
              >
                {isTracking ? 'Parar' : 'Iniciar'}
              </Button>
            </div>
            {currentLocation && (
              <div className="mt-3 text-sm text-gray-600">
                <p>Precisão: {currentLocation.accuracy?.toFixed(0)}m</p>
                {currentLocation.speed && (
                  <p>Velocidade: {(currentLocation.speed * 3.6).toFixed(1)} km/h</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <NavigationIcon className="h-5 w-5 mr-2" />
              Controle de Viagem
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Badge variant={tripId ? "default" : "secondary"}>
                  {tripId ? 'Em viagem' : 'Parado'}
                </Badge>
              </div>
              <Button
                variant={tripId ? "destructive" : "default"}
                size="sm"
                onClick={tripId ? handleStopTrip : handleStartTrip}
                disabled={!isTracking}
              >
                {tripId ? (
                  <>
                    <Square className="h-4 w-4 mr-1" />
                    Finalizar
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Iniciar
                  </>
                )}
              </Button>
            </div>
            {tripId && (
              <div className="mt-3 text-sm text-gray-600">
                <p>ID da viagem: {tripId.split('_')[2]}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Profile Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <Fuel className="h-5 w-5 mr-2" />
              Combustível
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">
              {getFuelTypeDisplay(profile?.preferred_fuel_type)}
            </p>
            <p className="text-sm text-gray-600 mt-1">Preferência atual</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              Notificações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">
              {profile?.notification_enabled ? 'Ativas' : 'Inativas'}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              A cada {profile?.notification_interval_km}km
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <TrendingDown className="h-5 w-5 mr-2" />
              Distância
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-purple-600">
              {profile?.total_distance_km?.toFixed(1) || '0.0'}km
            </p>
            <p className="text-sm text-gray-600 mt-1">Total percorrido</p>
          </CardContent>
        </Card>
      </div>

      {/* Last Notification */}
      {lastNotification && (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center text-green-800">
              <CheckCircle className="h-5 w-5 mr-2" />
              Último Posto Recomendado
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-green-900">{lastNotification.name}</h3>
                <p className="text-sm text-green-700">{lastNotification.address}</p>
                <p className="text-sm text-green-600 mt-1">
                  Distância: {lastNotification.distance_km?.toFixed(1)}km
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-green-800">
                  R$ {lastNotification.fuel_price?.price?.toFixed(2)}
                </p>
                <p className="text-sm text-green-600">por litro</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Nearby Stations */}
      {nearbyStations.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <MapPin className="h-5 w-5 mr-2" />
              Postos Próximos
            </CardTitle>
            <CardDescription>
              Postos de combustível na sua região
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {nearbyStations.slice(0, 3).map((station) => (
                <div key={station.id} className="flex justify-between items-center p-3 border rounded-lg">
                  <div>
                    <h4 className="font-medium">{station.name}</h4>
                    <p className="text-sm text-gray-600">{station.brand}</p>
                    <p className="text-sm text-gray-500">
                      {station.distance_km?.toFixed(1)}km de distância
                    </p>
                  </div>
                  {station.fuel_price && (
                    <div className="text-right">
                      <p className="font-bold text-blue-600">
                        R$ {station.fuel_price.price?.toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {getFuelTypeDisplay(station.fuel_price.fuel_type)}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Notifications */}
      {notifications.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              Notificações Recentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {notifications.slice(0, 3).map((notification) => (
                <div key={notification.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <div className="bg-blue-100 p-2 rounded-full">
                    <Fuel className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium">{notification.title}</h4>
                    <p className="text-sm text-gray-600">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(notification.sent_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                  {!notification.read_at && (
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isTracking && nearbyStations.length === 0 && notifications.length === 0 && (
        <Card className="text-center py-8">
          <CardContent>
            <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Ative o GPS para começar
            </h3>
            <p className="text-gray-600 mb-4">
              Permita o acesso à localização para receber recomendações de postos próximos
            </p>
            <Button onClick={startTracking}>
              Ativar GPS
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Dashboard

