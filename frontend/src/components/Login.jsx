import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Fuel, Mail, Lock, Loader2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuth()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await login(formData.email, formData.password)
      
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <Fuel className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Tanque Cheio</h1>
          <p className="text-gray-600 mt-2">Encontre os melhores preços de combustível</p>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader>
            <CardTitle>Entrar na sua conta</CardTitle>
            <CardDescription>
              Digite suas credenciais para acessar o aplicativo
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
                    Entrando...
                  </>
                ) : (
                  'Entrar'
                )}
              </Button>
              
              <div className="text-center text-sm text-gray-600">
                Não tem uma conta?{' '}
                <Link 
                  to="/register" 
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  Cadastre-se
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Features */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 mb-4">Com o Tanque Cheio você pode:</p>
          <div className="grid grid-cols-1 gap-2 text-sm text-gray-600">
            <div className="flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
              Receber notificações automáticas de postos baratos
            </div>
            <div className="flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
              Configurar seu combustível preferido
            </div>
            <div className="flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
              Economizar dinheiro em cada abastecimento
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login

