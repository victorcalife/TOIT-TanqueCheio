import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  MapPin, 
  Fuel, 
  Search, 
  Filter,
  Star,
  Clock,
  Phone,
  Navigation as NavigationIcon,
  DollarSign,
  Loader2
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useLocation } from '../contexts/LocationContext'

const GasStations = () => {
  const { profile } = useAuth()
  const { currentLocation } = useLocation()
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFuelType, setSelectedFuelType] = useState('')
  const [selectedBrand, setSelectedBrand] = useState('')
  const [sortBy, setSortBy] = useState('distance')
  const [page, setPage] = useState(1)

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api'

  const fuelTypes = [
    { value: '', label: 'Todos os combustíveis' },
    { value: 'gasoline', label: 'Gasolina' },
    { value: 'ethanol', label: 'Etanol' },
    { value: 'diesel', label: 'Diesel' },
    { value: 'diesel_s10', label: 'Diesel S10' },
    { value: 'gnv', label: 'GNV' }
  ]

  const brands = [
    { value: '', label: 'Todas as marcas' },
    { value: 'Shell', label: 'Shell' },
    { value: 'Petrobras', label: 'Petrobras' },
    { value: 'Ipiranga', label: 'Ipiranga' },
    { value: 'Raizen', label: 'Raízen' },
    { value: 'Ale', label: 'Ale' }
  ]

  const sortOptions = [
    { value: 'distance', label: 'Distância' },
    { value: 'price', label: 'Menor preço' },
    { value: 'name', label: 'Nome' },
    { value: 'brand', label: 'Marca' }
  ]

  useEffect(() => {
    fetchStations()
  }, [currentLocation, selectedFuelType, selectedBrand, sortBy, page])

  const fetchStations = async () => {
    setLoading(true)
    try {
      let url = `${API_BASE_URL}/gas-stations/?page=${page}&per_page=20`
      
      // Add location parameters if available
      if (currentLocation) {
        url += `&latitude=${currentLocation.latitude}&longitude=${currentLocation.longitude}&radius_km=50`
      }
      
      // Add filters
      if (selectedFuelType) {
        url += `&fuel_type=${selectedFuelType}`
      }
      if (selectedBrand) {
        url += `&brand=${selectedBrand}`
      }
      if (searchTerm) {
        url += `&search=${encodeURIComponent(searchTerm)}`
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setStations(data.data.gas_stations)
        }
      }
    } catch (error) {
      console.error('Error fetching stations:', error)
    } finally {
      setLoading(false)
    }
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

  const getLowestPrice = (station) => {
    if (!station.current_prices || station.current_prices.length === 0) {
      return null
    }
    
    const prices = station.current_prices
    const lowestPrice = Math.min(...prices.map(p => p.price))
    const lowestPriceItem = prices.find(p => p.price === lowestPrice)
    
    return lowestPriceItem
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchStations()
  }

  const handleReset = () => {
    setSearchTerm('')
    setSelectedFuelType('')
    setSelectedBrand('')
    setSortBy('distance')
    setPage(1)
  }

  return (
    <div className="container mx-auto px-4 py-6 pb-20 md:pb-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Postos de Combustível
        </h1>
        <p className="text-gray-600 mt-1">
          Encontre os melhores preços na sua região
        </p>
      </div>

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="h-5 w-5 mr-2" />
            Buscar Postos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Search Input */}
            <div className="flex gap-2">
              <Input
                placeholder="Buscar por nome, endereço ou marca..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Select value={selectedFuelType} onValueChange={setSelectedFuelType}>
                <SelectTrigger>
                  <SelectValue placeholder="Combustível" />
                </SelectTrigger>
                <SelectContent>
                  {fuelTypes.map((fuel) => (
                    <SelectItem key={fuel.value} value={fuel.value}>
                      {fuel.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={selectedBrand} onValueChange={setSelectedBrand}>
                <SelectTrigger>
                  <SelectValue placeholder="Marca" />
                </SelectTrigger>
                <SelectContent>
                  {brands.map((brand) => (
                    <SelectItem key={brand.value} value={brand.value}>
                      {brand.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue placeholder="Ordenar por" />
                </SelectTrigger>
                <SelectContent>
                  {sortOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button variant="outline" onClick={handleReset}>
                <Filter className="h-4 w-4 mr-2" />
                Limpar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Location Status */}
      {!currentLocation && (
        <Card className="mb-6 border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-yellow-800">
              <MapPin className="h-5 w-5" />
              <p className="text-sm">
                Ative o GPS para ver postos próximos e calcular distâncias
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stations List */}
      <div className="space-y-4">
        {loading && stations.length === 0 ? (
          <div className="text-center py-8">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">Carregando postos...</p>
          </div>
        ) : stations.length === 0 ? (
          <Card className="text-center py-8">
            <CardContent>
              <Fuel className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhum posto encontrado
              </h3>
              <p className="text-gray-600 mb-4">
                Tente ajustar os filtros ou buscar por outros termos
              </p>
              <Button onClick={handleReset} variant="outline">
                Limpar filtros
              </Button>
            </CardContent>
          </Card>
        ) : (
          stations.map((station) => {
            const lowestPrice = getLowestPrice(station)
            
            return (
              <Card key={station.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {station.name}
                        </h3>
                        {station.brand && (
                          <Badge variant="secondary">{station.brand}</Badge>
                        )}
                      </div>
                      
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <MapPin className="h-4 w-4" />
                          <span>{station.address}</span>
                        </div>
                        
                        {station.phone && (
                          <div className="flex items-center space-x-2">
                            <Phone className="h-4 w-4" />
                            <span>{station.phone}</span>
                          </div>
                        )}
                        
                        {station.distance_km && (
                          <div className="flex items-center space-x-2">
                            <NavigationIcon className="h-4 w-4" />
                            <span>{station.distance_km.toFixed(1)} km de distância</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Price Display */}
                    {lowestPrice && (
                      <div className="text-right">
                        <div className="text-2xl font-bold text-green-600">
                          R$ {lowestPrice.price.toFixed(2)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {getFuelTypeDisplay(lowestPrice.fuel_type)}
                        </div>
                        <div className="text-xs text-gray-500">
                          por litro
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Fuel Prices */}
                  {station.current_prices && station.current_prices.length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Preços dos Combustíveis
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                        {station.current_prices.map((price) => (
                          <div key={price.id} className="bg-gray-50 rounded-lg p-3 text-center">
                            <div className="text-sm font-medium text-gray-900">
                              {getFuelTypeDisplay(price.fuel_type)}
                            </div>
                            <div className="text-lg font-bold text-blue-600">
                              R$ {price.price.toFixed(2)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(price.reported_at).toLocaleDateString('pt-BR')}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Amenities */}
                  {station.amenities && station.amenities.length > 0 && (
                    <div className="border-t pt-4 mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        Serviços
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {station.amenities.map((amenity) => (
                          <Badge key={amenity} variant="outline" className="text-xs">
                            {amenity.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Active Coupons */}
                  {station.active_coupons && station.active_coupons.length > 0 && (
                    <div className="border-t pt-4 mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">
                        Cupons Disponíveis
                      </h4>
                      <div className="space-y-2">
                        {station.active_coupons.map((coupon) => (
                          <div key={coupon.id} className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-medium text-green-800">
                                  {coupon.title}
                                </div>
                                <div className="text-sm text-green-600">
                                  {coupon.description}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="font-bold text-green-800">
                                  {coupon.discount_type === 'percentage' ? 
                                    `${coupon.discount_value}%` : 
                                    `R$ ${coupon.discount_value.toFixed(2)}`
                                  }
                                </div>
                                <div className="text-xs text-green-600">
                                  desconto
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })
        )}
      </div>

      {/* Load More Button */}
      {stations.length > 0 && stations.length % 20 === 0 && (
        <div className="text-center mt-6">
          <Button 
            onClick={() => {
              setPage(prev => prev + 1)
              fetchStations()
            }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Carregando...
              </>
            ) : (
              'Carregar mais postos'
            )}
          </Button>
        </div>
      )}
    </div>
  )
}

export default GasStations

