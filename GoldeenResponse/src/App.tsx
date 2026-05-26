import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { 
  HeartPulse, LayoutDashboard, BedIcon, Users, Settings, 
  BellRing, Search, LogOut, Menu, Activity
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import WardManagement from './components/WardManagement';
import StaffManagement from './components/StaffManagement';
import EquipmentManagement from './components/EquipmentManagement';
import Login from './components/Login';

// Ensure socket connects to the correct host/port. In production, this matches window.location
export const socket = io(import.meta.env.VITE_APP_URL || '', {
  path: '/socket.io/',
});

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    function onConnect() { setIsConnected(true); }
    function onDisconnect() { setIsConnected(false); }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoadingAuth(false);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, []);

  const handleLogin = (token: string) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  if (loadingAuth) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex overflow-hidden font-sans text-slate-900">
      
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col hidden md:flex h-full">
        <div className="h-16 flex items-center px-6 border-b border-slate-800 shrink-0">
          <HeartPulse className="w-6 h-6 text-blue-500 mr-2" />
          <span className="text-lg font-semibold tracking-tight text-white">MedCore HBRMS</span>
        </div>
        
        <div className="p-4 flex-1 overflow-y-auto space-y-1">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors cursor-pointer ${activeTab === 'dashboard' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
          >
            <LayoutDashboard className="w-5 h-5 mr-3 shrink-0" />
            <span>Dashboard</span>
          </button>
          <button 
            onClick={() => setActiveTab('wards')}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors cursor-pointer ${activeTab === 'wards' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
          >
            <BedIcon className="w-5 h-5 mr-3 shrink-0" />
            <span>Bed Allocation</span>
          </button>
          <button 
            onClick={() => setActiveTab('staff')}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors cursor-pointer ${activeTab === 'staff' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
          >
            <Users className="w-5 h-5 mr-3 shrink-0" />
            <span>Staff & Shifts</span>
          </button>
          <button 
            onClick={() => setActiveTab('equipments')}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors cursor-pointer ${activeTab === 'equipments' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
          >
            <Activity className="w-5 h-5 mr-3 shrink-0" />
            <span>Equipments</span>
          </button>
        </div>

        <div className="p-6 border-t border-slate-800 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center text-xs text-white">AD</div>
          <div className="flex flex-col">
            <span className="text-sm text-white font-medium">Admin User</span>
            <span className="text-xs text-slate-500">Lead Administrator</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shrink-0 relative z-10">
          <div className="flex items-center">
            <button className="md:hidden text-slate-500 hover:text-slate-700 mr-4">
              <Menu className="w-6 h-6" />
            </button>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search patient, bed, or staff..." 
                className="pl-9 pr-4 py-2 bg-slate-50 border-transparent rounded-full text-sm w-64 md:w-80 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center hidden sm:flex">
              <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {isConnected ? 'System Live' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              <span className="text-xs font-bold text-red-500 uppercase">4 Critical Alerts</span>
            </div>
            <div className="relative">
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative text-slate-500 hover:text-slate-700"
              >
                <BellRing className="w-5 h-5" />
              </button>
              
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50">
                  <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                    <h3 className="font-bold text-slate-900">Notifications</h3>
                    <span className="text-xs text-blue-600 font-bold cursor-pointer hover:text-blue-800">Mark all as read</span>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    <div className="p-4 border-b border-slate-50 hover:bg-slate-50 transition-colors">
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-red-500 mr-3"></div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">Ventilator Threshold Alert</p>
                          <p className="text-xs text-slate-500 mt-1">Only 3 units remaining in South Wing cache. Allocation restricted.</p>
                          <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">6 mins ago</p>
                        </div>
                      </div>
                    </div>
                    <div className="p-4 border-b border-slate-50 hover:bg-slate-50 transition-colors">
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-amber-500 mr-3"></div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">Shift Transition Delay</p>
                          <p className="text-xs text-slate-500 mt-1">Nurse team delta-7 reporting 15min delay in handoff reporting.</p>
                          <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">42 mins ago</p>
                        </div>
                      </div>
                    </div>
                    <div className="p-4 hover:bg-slate-50 transition-colors">
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-blue-500 mr-3"></div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">Oxygen Resupply Inbound</p>
                          <p className="text-xs text-slate-500 mt-1">Medical delivery vehicle #92 arrives at Dock B in 12 min.</p>
                          <p className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">1 hour ago</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 border-t border-slate-100 text-center bg-slate-50 cursor-pointer hover:bg-slate-100 transition-colors">
                    <span className="text-xs font-bold text-slate-600">View All Notifications</span>
                  </div>
                </div>
              )}
            </div>
            <button onClick={handleLogout} className="relative text-slate-500 hover:text-slate-700 ml-4 border-l border-slate-200 pl-4 flex items-center transition-colors">
              <LogOut className="w-5 h-5 mr-1" />
              <span className="text-xs font-bold uppercase tracking-wider">Logout</span>
            </button>
          </div>
        </header>

        {/* Scrollable Canvas */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'wards' && <WardManagement />}
            {activeTab === 'staff' && <StaffManagement />}
            {activeTab === 'equipments' && <EquipmentManagement />}
          </div>
        </div>
      </main>

    </div>
  );
}
