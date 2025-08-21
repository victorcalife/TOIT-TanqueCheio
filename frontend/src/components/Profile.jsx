import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { 
  User, 
  Mail, 
  Phone, 
  Fuel, 
  Bell, 
  MapPin, 
  Save,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const Profile = () => {
  const { user, profile, updateProfile } = useAuth()
  const [formData, setFormData] = useState({
    preferred_fuel_type: 'gasoline',
    notification_enabled: true,
    notification_interval_km: 100,
    notification_radius_km: 50
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  const fuelTypes = [
    { value: 'gasoline', label: 'Gasolina' },
    { value: 'ethanol', label: 'Etanol' },
    { value: 'diesel', label: 'Diesel' },
    { value: 'diesel_s10', label: 'Diesel S10' },
    { value: 'gnv', label: 'GNV' }
  ]

  const intervalOptions = [
    { value: 50, label: '50 km' },
    { value: 100, label: '100 km' },
    { value: 150, label: '150 km' },
    { value: 200, label: '200 km' },
    { value: 300, label: '300 km' }
  ]

  const radiusOptions = [
    { value: 10, label: '10 km' },
    { value: 25, label: '25 km' },
    { value: 50, label: '50 km' },
    { value: 75, label: '75 km' },
    { value: 100, label: '100 km' }
  ]

  useEffect(() => {
    if (profile) {
      setFormData({
        preferred_fuel_type: profile.preferred_fuel_type || 'gasoline',
        notification_enabled: profile.notification_enabled || true,
        notification_interval_km: profile.notification_interval_km || 100,
        notification_radius_km: profile.notification_radius_km || 50
      })
    }
  }, [profile])

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const result = await updateProfile(formData)
      
      if (result.success) {
        setMessage({ 
          type: 'success', 
          text: 'Perfil atualizado com sucesso!' 
        })
      } else {
        setMessage({ 
          type: 'error', 
          text: result.error || 'Erro ao atualizar perfil' 
        })
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: 'Erro inesperado. Tente novamente.' 
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-6 pb-20 md:pb-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            Meu Perfil
          </h1>
          <p className="text-gray-600 mt-1">
            Configure suas preferências e notificações
          </p>
        </div>

        {/* User Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              Informações Pessoais
            </CardTitle>
            <CardDescription>
              Suas informações básicas de cadastro
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nome</Label>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-gray-400" />
                  <span className="text-sm">{user?.name}</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>E-mail</Label>
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span className="text-sm">{user?.email}</span>
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Para alterar essas informações, entre em contato com o suporte.
            </div>
          </CardContent>
        </Card>

        {/* Preferences Form */}
        <form onSubmit={handleSubmit}>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Fuel className="h-5 w-5 mr-2" />
                Preferências de Combustível
              </CardTitle>
              <CardDescription>
                Configure seu tipo de combustível preferido
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="fuel_type">Combustível Preferido</Label>
                <Select 
                  value={formData.preferred_fuel_type} 
                  onValueChange={(value) => handleChange('preferred_fuel_type', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o combustível" />
                  </SelectTrigger>
                  <SelectContent>
                    {fuelTypes.map((fuel) => (
                      <SelectItem key={fuel.value} value={fuel.value}>
                        {fuel.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500">
                  Este será o combustível usado nas recomendações automáticas
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="h-5 w-5 mr-2" />
                Configurações de Notificação
              </CardTitle>
              <CardDescription>
                Configure quando e como receber notificações
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Enable Notifications */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Notificações Automáticas</Label>
                  <p className="text-sm text-gray-500">
                    Receber notificações de postos baratos durante viagens
                  </p>
                </div>
                <Switch
                  checked={formData.notification_enabled}
                  onCheckedChange={(checked) => handleChange('notification_enabled', checked)}
                />
              </div>

              <Separator />

              {/* Notification Interval */}
              <div className="space-y-2">
                <Label>Intervalo de Notificação</Label>
                <Select 
                  value={formData.notification_interval_km.toString()} 
                  onValueChange={(value) => handleChange('notification_interval_km', parseInt(value))}
                  disabled={!formData.notification_enabled}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o intervalo" />
                  </SelectTrigger>
                  <SelectContent>
                    {intervalOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500">
                  Frequência para receber notificações baseada na distância percorrida
                </p>
              </div>

              {/* Search Radius */}
              <div className="space-y-2">
                <Label>Raio de Busca</Label>
                <Select 
                  value={formData.notification_radius_km.toString()} 
                  onValueChange={(value) => handleChange('notification_radius_km', parseInt(value))}
                  disabled={!formData.notification_enabled}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o raio" />
                  </SelectTrigger>
                  <SelectContent>
                    {radiusOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500">
                  Distância máxima para buscar postos de combustível
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Statistics */}
          {profile && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="h-5 w-5 mr-2" />
                  Estatísticas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {profile.total_distance_km?.toFixed(1) || '0.0'}
                    </p>
                    <p className="text-sm text-gray-600">km percorridos</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {profile.distance_until_next_notification?.toFixed(0) || '0'}
                    </p>
                    <p className="text-sm text-gray-600">km até próxima notificação</p>
                  </div>
                  <div className="text-center md:col-span-1 col-span-2">
                    <p className="text-2xl font-bold text-purple-600">
                      {profile.last_location_update ? 'Ativo' : 'Inativo'}
                    </p>
                    <p className="text-sm text-gray-600">Status GPS</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Message */}
          {message.text && (
            <Alert variant={message.type === 'error' ? 'destructive' : 'default'} className="mb-6">
              {message.type === 'success' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>{message.text}</AlertDescription>
            </Alert>
          )}

          {/* Save Button */}
          <div className="flex justify-end">
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Salvar Alterações
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Profile

