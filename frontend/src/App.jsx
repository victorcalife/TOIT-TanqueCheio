import React, { useState, useEffect } from 'react';
import './App.css';
import { API_BASE_URL } from './config';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentView, setCurrentView] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Estados GPS
  const [gpsEnabled, setGpsEnabled] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [activeTrip, setActiveTrip] = useState(null);
  const [tripStatus, setTripStatus] = useState(null);
  
  // Estados do formulário
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  });
  
  // Estados de viagem
  const [tripData, setTripData] = useState({
    origin_address: 'Balneário Camboriú, SC',
    destination_address: 'São Paulo, SP',
    fuel_type: 'gasoline',
    notification_interval: 100
  });

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
      fetchTripStatus();
    }
  }, [token]);

  useEffect(() => {
    if (gpsEnabled && activeTrip) {
      const interval = setInterval(() => {
        updateGPSLocation();
      }, 10000); // Atualizar a cada 10 segundos

      return () => clearInterval(interval);
    }
  }, [gpsEnabled, activeTrip]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Erro ao buscar usuário:', error);
    }
  };

  const fetchTripStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/gps/trip-status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.has_active_trip) {
          setActiveTrip(data.trip);
          setTripStatus(data.trip);
        }
      }
    } catch (error) {
      console.error('Erro ao buscar status da viagem:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Tentando fazer login com:', { email: formData.email });
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      console.log('Resposta do servidor:', {
        status: response.status,
        statusText: response.statusText
      });

      const data = await response.json().catch(() => ({}));
      console.log('Dados da resposta:', data);

      if (!response.ok) {
        throw new Error(data.message || `Erro HTTP: ${response.status}`);
      }

      if (data.access_token) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setUser(data.user || { email: formData.email });
        setCurrentView('dashboard');
        setFormData({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
      } else {
        throw new Error(data.error || 'Credenciais inválidas');
      }
    } catch (error) {
      console.error('Erro no login:', error);
      alert(`Falha no login: ${error.message || 'Verifique suas credenciais e tente novamente'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      alert('Senhas não coincidem');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          password: formData.password
        })
      });

      const data = await response.json();

      if (data.success) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        setCurrentView('dashboard');
        setFormData({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
      } else {
        alert(data.error || 'Erro no cadastro');
      }
    } catch (error) {
      console.error('Erro no cadastro:', error);
      alert('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentView('login');
    setActiveTrip(null);
    setGpsEnabled(false);
  };

  const enableGPS = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
          setGpsEnabled(true);
          alert('GPS ativado com sucesso!');
        },
        (error) => {
          console.error('Erro ao obter localização:', error);
          alert('Erro ao ativar GPS. Usando localização simulada.');
          setCurrentLocation({
            latitude: -26.9906,
            longitude: -48.6356
          });
          setGpsEnabled(true);
        }
      );
    } else {
      alert('GPS não suportado. Usando localização simulada.');
      setCurrentLocation({
        latitude: -26.9906,
        longitude: -48.6356
      });
      setGpsEnabled(true);
    }
  };

  const startTrip = async () => {
    if (!gpsEnabled) {
      alert('Ative o GPS primeiro!');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/gps/start-trip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(tripData)
      });

      const data = await response.json();

      if (data.success) {
        setActiveTrip({
          id: data.trip_id,
          origin: tripData.origin_address,
          destination: tripData.destination_address,
          fuel_type: tripData.fuel_type,
          notification_interval: tripData.notification_interval,
          distance_traveled: 0
        });
        alert('Viagem iniciada! Você receberá notificações automáticas a cada ' + tripData.notification_interval + 'km.');
      } else {
        alert(data.error || 'Erro ao iniciar viagem');
      }
    } catch (error) {
      console.error('Erro ao iniciar viagem:', error);
      alert('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const updateGPSLocation = async () => {
    if (!currentLocation || !activeTrip) return;

    // Simular movimento (incrementar latitude gradualmente)
    const newLat = currentLocation.latitude + 0.01;
    const newLocation = {
      latitude: newLat,
      longitude: currentLocation.longitude
    };

    try {
      const response = await fetch(`${API_BASE_URL}/gps/update-location`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latitude: newLocation.latitude,
          longitude: newLocation.longitude,
          accuracy: 10,
          speed: 80
        })
      });

      const data = await response.json();

      if (data.success) {
        setCurrentLocation(newLocation);
        
        // Atualizar distância percorrida
        if (activeTrip) {
          setActiveTrip(prev => ({
            ...prev,
            distance_traveled: data.distance_traveled
          }));
        }

        // Mostrar notificação se enviada
        if (data.notification_sent) {
          showNotification(`⛽ Posto mais barato encontrado! ${data.distance_traveled}km percorridos.`);
        }
      }
    } catch (error) {
      console.error('Erro ao atualizar localização:', error);
    }
  };

  const stopTrip = async () => {
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/gps/stop-trip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        setActiveTrip(null);
        setGpsEnabled(false);
        alert(`Viagem finalizada! Distância total: ${data.trip_summary.distance_traveled}km`);
      } else {
        alert(data.error || 'Erro ao finalizar viagem');
      }
    } catch (error) {
      console.error('Erro ao finalizar viagem:', error);
      alert('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message) => {
    // Mostrar notificação do browser se suportado
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Tanque Cheio', {
        body: message,
        icon: '/favicon.ico'
      });
    } else {
      // Fallback para alert
      alert(message);
    }
  };

  // Solicitar permissão para notificações
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">⛽ Tanque Cheio</h1>
            <p className="text-gray-600">Sistema GPS de Combustível Inteligente</p>
          </div>

          {currentView === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <h2 className="text-xl font-semibold text-center mb-4">Entrar</h2>
              
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              
              <input
                type="password"
                placeholder="Senha"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Entrando...' : 'Entrar'}
              </button>
              
              <p className="text-center text-gray-600">
                Não tem conta?{' '}
                <button
                  type="button"
                  onClick={() => setCurrentView('register')}
                  className="text-blue-600 hover:underline font-medium"
                >
                  Cadastre-se
                </button>
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <h2 className="text-xl font-semibold text-center mb-4">Criar Conta</h2>
              
              <input
                type="text"
                placeholder="Nome completo"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              
              <input
                type="tel"
                placeholder="Telefone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              
              <input
                type="password"
                placeholder="Senha"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              
              <input
                type="password"
                placeholder="Confirmar senha"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 text-white p-3 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Criando...' : 'Criar Conta'}
              </button>
              
              <p className="text-center text-gray-600">
                Já tem conta?{' '}
                <button
                  type="button"
                  onClick={() => setCurrentView('login')}
                  className="text-green-600 hover:underline font-medium"
                >
                  Entre aqui
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-800">⛽ Tanque Cheio</h1>
              {activeTrip && (
                <span className="ml-4 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  🚗 Viagem Ativa
                </span>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Olá, {user?.name}</span>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Status GPS */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">🛰️ Status GPS</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className={`text-2xl mb-2 ${gpsEnabled ? 'text-green-500' : 'text-red-500'}`}>
                {gpsEnabled ? '✅' : '❌'}
              </div>
              <p className="text-sm text-gray-600">GPS {gpsEnabled ? 'Ativo' : 'Inativo'}</p>
            </div>
            <div className="text-center">
              <div className={`text-2xl mb-2 ${activeTrip ? 'text-blue-500' : 'text-gray-400'}`}>
                🚗
              </div>
              <p className="text-sm text-gray-600">
                {activeTrip ? 'Em Viagem' : 'Parado'}
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2 text-purple-500">
                📍
              </div>
              <p className="text-sm text-gray-600">
                {currentLocation ? 
                  `${currentLocation.latitude.toFixed(4)}, ${currentLocation.longitude.toFixed(4)}` :
                  'Sem localização'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Controles de Viagem */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">🗺️ Controle de Viagem</h2>
          
          {!activeTrip ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Origem
                  </label>
                  <input
                    type="text"
                    value={tripData.origin_address}
                    onChange={(e) => setTripData({...tripData, origin_address: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Destino
                  </label>
                  <input
                    type="text"
                    value={tripData.destination_address}
                    onChange={(e) => setTripData({...tripData, destination_address: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Combustível
                  </label>
                  <select
                    value={tripData.fuel_type}
                    onChange={(e) => setTripData({...tripData, fuel_type: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gasoline">Gasolina</option>
                    <option value="ethanol">Etanol</option>
                    <option value="diesel">Diesel</option>
                    <option value="diesel_s10">Diesel S10</option>
                    <option value="gnv">GNV</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notificar a cada (km)
                  </label>
                  <select
                    value={tripData.notification_interval}
                    onChange={(e) => setTripData({...tripData, notification_interval: parseInt(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={50}>50 km</option>
                    <option value={100}>100 km</option>
                    <option value={150}>150 km</option>
                    <option value={200}>200 km</option>
                    <option value={300}>300 km</option>
                  </select>
                </div>
              </div>
              
              <div className="flex space-x-4">
                {!gpsEnabled ? (
                  <button
                    onClick={enableGPS}
                    className="flex-1 bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 font-medium"
                  >
                    🛰️ Ativar GPS
                  </button>
                ) : (
                  <button
                    onClick={startTrip}
                    disabled={loading}
                    className="flex-1 bg-green-600 text-white p-3 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                  >
                    {loading ? 'Iniciando...' : '🚀 Iniciar Viagem'}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800 mb-2">Viagem em Andamento</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><strong>Origem:</strong> {activeTrip.origin}</p>
                    <p><strong>Destino:</strong> {activeTrip.destination}</p>
                  </div>
                  <div>
                    <p><strong>Combustível:</strong> {activeTrip.fuel_type}</p>
                    <p><strong>Distância:</strong> {activeTrip.distance_traveled}km</p>
                  </div>
                </div>
              </div>
              
              <button
                onClick={stopTrip}
                disabled={loading}
                className="w-full bg-red-600 text-white p-3 rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Finalizando...' : '🛑 Finalizar Viagem'}
              </button>
            </div>
          )}
        </div>

        {/* Informações do Sistema */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">ℹ️ Como Funciona</h2>
          <div className="space-y-3 text-gray-600">
            <p>• <strong>Ative o GPS</strong> para permitir o rastreamento da sua localização</p>
            <p>• <strong>Configure sua viagem</strong> com origem, destino e tipo de combustível</p>
            <p>• <strong>Inicie a viagem</strong> e receba notificações automáticas dos postos mais baratos</p>
            <p>• <strong>Notificações inteligentes</strong> baseadas na distância configurada (ex: a cada 100km)</p>
            <p>• <strong>Economia garantida</strong> com os melhores preços na sua rota</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

