import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Fuel, Mail, Lock, User, Phone, Loader2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    preferred_fuel_type: 'gasoline'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register } = useAuth()

  const fuelTypes = [
    { value: 'gasoline', label: 'Gasolina' },
    { value: 'ethanol', label: 'Etanol' },
    { value: 'diesel', label: 'Diesel' },
    { value: 'diesel_s10', label: 'Diesel S10' },
    { value: 'gnv', label: 'GNV' }
  ]

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleFuelTypeChange = (value) => {
    setFormData({
      ...formData,
      preferred_fuel_type: value
    })
  }

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('As senhas não coincidem')
      return false
    }
    
    if (formData.password.length < 8) {
      setError('A senha deve ter pelo menos 8 caracteres')
      return false
    }
    
    if (!formData.name.trim()) {
      setError('Nome é obrigatório')
      return false
    }
    
    if (!formData.phone.trim()) {
      setError('Telefone é obrigatório')
      return false
    }
    
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    if (!validateForm()) {
      return
    }
    
    setLoading(true)

    try {
      const { confirmPassword, ...registerData } = formData
      const result = await register(registerData)
      
      if (!result.success) {
        setError(result.error)
      }
    } catch (error) {
      setError('Erro inesperado. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-8">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <Fuel className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Tanque Cheio</h1>
          <p className="text-gray-600 mt-2">Crie sua conta e comece a economizar</p>
        </div>

        {/* Register Form */}
        <Card>
          <CardHeader>
            <CardTitle>Criar conta</CardTitle>
            <CardDescription>
              Preencha seus dados para se cadastrar
            </CardDescription>
          </CardHeader>
          
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="name">Nome completo</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Seu nome completo"
                    value={formData.name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="seu@email.com"
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="phone">Telefone</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="+55 11 99999-9999"
                    value={formData.phone}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="preferred_fuel_type">Combustível preferido</Label>
                <Select value={formData.preferred_fuel_type} onValueChange={handleFuelTypeChange}>
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
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Senha</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar senha</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
            </CardContent>
            
            <CardFooter className="flex flex-col space-y-4">
              <Button 
                type="submit" 
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Criando conta...
                  </>
                ) : (
                  'Criar conta'
                )}
              </Button>
              
              <div className="text-center text-sm text-gray-600">
                Já tem uma conta?{' '}
                <Link 
                  to="/login" 
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  Faça login
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Privacy Note */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Ao criar uma conta, você concorda com nossos{' '}
            <a href="#" className="text-blue-600 hover:text-blue-500">
              Termos de Uso
            </a>{' '}
            e{' '}
            <a href="#" className="text-blue-600 hover:text-blue-500">
              Política de Privacidade
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register

