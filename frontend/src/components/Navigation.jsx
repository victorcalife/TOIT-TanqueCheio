import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { 
  Fuel, 
  Home, 
  MapPin, 
  User, 
  LogOut, 
  Menu, 
  X,
  Bell,
  Settings
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useLocation as useGPSLocation } from '../contexts/LocationContext'

const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  const { user, logout } = useAuth()
  const { isTracking, currentLocation } = useGPSLocation()

  const navItems = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: Home
    },
    {
      path: '/gas-stations',
      label: 'Postos',
      icon: MapPin
    },
    {
      path: '/profile',
      label: 'Perfil',
      icon: User
    }
  ]

  const isActive = (path) => location.pathname === path

  const handleLogout = () => {
    logout()
    setIsOpen(false)
  }

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex fixed top-0 left-0 right-0 bg-white shadow-sm border-b z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/dashboard" className="flex items-center space-x-2">
                <div className="bg-blue-600 p-2 rounded-lg">
                  <Fuel className="h-6 w-6 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">Tanque Cheio</span>
              </Link>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center space-x-4">
              {navItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              {/* GPS Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isTracking ? 'bg-green-500' : 'bg-gray-400'
                }`}></div>
                <span className="text-xs text-gray-500">
                  {isTracking ? 'GPS Ativo' : 'GPS Inativo'}
                </span>
              </div>

              {/* User Info */}
              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <nav className="md:hidden fixed top-0 left-0 right-0 bg-white shadow-sm border-b z-50">
        <div className="px-4">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Fuel className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">Tanque Cheio</span>
            </Link>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-600"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="bg-white border-t">
            <div className="px-4 py-2 space-y-1">
              {/* GPS Status */}
              <div className="flex items-center justify-between py-2 border-b">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    isTracking ? 'bg-green-500' : 'bg-gray-400'
                  }`}></div>
                  <span className="text-sm text-gray-600">
                    {isTracking ? 'GPS Ativo' : 'GPS Inativo'}
                  </span>
                </div>
                {currentLocation && (
                  <span className="text-xs text-gray-500">
                    {currentLocation.accuracy?.toFixed(0)}m
                  </span>
                )}
              </div>

              {/* Navigation Items */}
              {navItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center space-x-3 px-3 py-3 rounded-md text-base font-medium transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}

              {/* User Info */}
              <div className="border-t pt-4 mt-4">
                <div className="flex items-center space-x-3 px-3 py-2">
                  <div className="bg-gray-200 p-2 rounded-full">
                    <User className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                </div>
                
                <Button
                  variant="ghost"
                  onClick={handleLogout}
                  className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 mt-2"
                >
                  <LogOut className="h-4 w-4 mr-3" />
                  Sair
                </Button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Bottom Navigation for Mobile */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t z-40">
        <div className="grid grid-cols-3 h-16">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center space-y-1 ${
                  isActive(item.path)
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-600'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </>
  )
}

export default Navigation

