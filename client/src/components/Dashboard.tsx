import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { Activity, AlertTriangle, ArrowUpRight, BedIcon, Users } from 'lucide-react';
import { socket } from '../App';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalBeds: 0,
    occupiedBeds: 0,
    vacantBeds: 0,
    occupancyRate: 0,
    icuTotal: 0,
    icuOccupied: 0,
    icuVacant: 0,
    icuOccupancyRate: 0,
  });

  const [loading, setLoading] = useState(true);

  // Note: in a real app these would be fetched from API and kept up to date
  const timeSeriesData = [
    { time: '08:00', icu: 15, general: 45 },
    { time: '10:00', icu: 18, general: 48 },
    { time: '12:00', icu: 20, general: 44 },
    { time: '14:00', icu: 22, general: 51 },
    { time: '16:00', icu: 21, general: 53 },
    { time: '18:00', icu: 23, general: 55 },
    { time: '20:00', icu: 24, general: 60 },
  ];

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      setStats(data);
      setLoading(false);
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Listen for real-time bed updates to refresh stats
    socket.on('bedUpdated', () => {
      fetchStats();
    });

    return () => {
      socket.off('bedUpdated');
    };
  }, []);

  const pieData = [
    { name: 'Occupied', value: stats.occupiedBeds, color: '#3b82f6' }, // blue-500
    { name: 'Vacant', value: stats.vacantBeds, color: '#e2e8f0' }, // slate-200
  ];

  return (
    <div className="space-y-6">
      
      {/* Header section */}
      <div className="hidden">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Hospital Overview</h1>
        <p className="text-slate-500 text-sm mt-1">Live occupancy metrics and resource utilization.</p>
      </div>

      {/* Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card 1 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase">Total Occupancy</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-3xl font-bold text-slate-900">{loading ? '-' : `${stats.occupancyRate}%`}</h2>
            <span className="text-blue-600 font-bold text-sm flex items-center">
              <ArrowUpRight className="w-4 h-4 mr-0.5" /> 2.1%
            </span>
          </div>
          <div className="mt-4 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600" style={{ width: `${stats.occupancyRate || 0}%` }}></div>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase">ICU Capacity</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-3xl font-bold text-slate-900">{loading ? '-' : `${stats.icuOccupied} / ${stats.icuTotal}`}</h2>
            <span className={`${stats.icuOccupancyRate > 85 ? 'text-red-500' : 'text-orange-500'} font-bold text-sm`}>
              {stats.icuOccupancyRate}% utilized
            </span>
          </div>
          <div className="mt-4 flex space-x-1">
            <div className="h-1.5 flex-1 bg-blue-500 rounded-full"></div>
            <div className="h-1.5 flex-1 bg-blue-500 rounded-full"></div>
            <div className="h-1.5 flex-1 bg-blue-500 rounded-full"></div>
            <div className="h-1.5 flex-1 bg-slate-100 rounded-full"></div>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase">Active Staff</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-3xl font-bold text-slate-900">42</h2>
            <span className="text-slate-400 font-bold text-sm">On Duty</span>
          </div>
          <div className="mt-4 flex -space-x-2">
            <img className="w-8 h-8 rounded-full border-2 border-white" src="https://ui-avatars.com/api/?name=Jane+Doe&background=eff6ff&color=1d4ed8" alt="Jane" />
            <img className="w-8 h-8 rounded-full border-2 border-white" src="https://ui-avatars.com/api/?name=John+Smith&background=f0fdf4&color=15803d" alt="John" />
            <img className="w-8 h-8 rounded-full border-2 border-white" src="https://ui-avatars.com/api/?name=Sarah+Connor&background=fef2f2&color=b91c1c" alt="Sarah" />
            <img className="w-8 h-8 rounded-full border-2 border-white" src="https://ui-avatars.com/api/?name=Mike+Chang&background=fffbeb&color=b45309" alt="Mike" />
            <div className="w-8 h-8 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-slate-600">+38</div>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-blue-600 p-5 rounded-xl shadow-lg text-white">
          <p className="text-xs font-semibold opacity-70 uppercase">Emergency Intake</p>
          <div className="mt-2">
            <h2 className="text-3xl font-bold">Level 2</h2>
            <p className="text-xs mt-1 font-medium">Surge protocol currently active</p>
          </div>
          <button className="mt-3 w-full py-2 bg-white/20 rounded-lg text-xs font-bold hover:bg-white/30 transition-colors">View Disaster Plan</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Main Chart area - Admission Trends */}
        <div className="col-span-1 lg:col-span-8 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900">Admission Trends (Today)</h3>
            <div className="flex space-x-2">
              <span className="flex items-center text-xs text-slate-500 font-medium"><span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>General</span>
              <span className="flex items-center text-xs text-slate-500 font-medium"><span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>ICU</span>
            </div>
          </div>
          <div className="flex-1 p-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timeSeriesData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  cursor={{ fill: '#f8fafc' }}
                />
                <Bar dataKey="general" name="General" stackId="a" fill="#3b82f6" radius={[0, 0, 4, 4]} />
                <Bar dataKey="icu" name="ICU" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Sidebar: Alerts & Donut Chart */}
        <div className="col-span-1 lg:col-span-4 flex flex-col gap-6">
          
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-red-600 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2" />
                System Alerts
              </h3>
              <span className="text-[10px] bg-slate-100 px-2 py-1 rounded font-bold text-slate-600">LIVE</span>
            </div>
            <div className="space-y-3">
              {stats.icuOccupancyRate > 85 && (
                <div className="p-3 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
                  <p className="text-xs font-bold text-red-900">ICU Capacity Critical</p>
                  <p className="text-[10px] text-red-700 mt-1">Only {stats.icuVacant} beds available. Consider diversion protocols.</p>
                </div>
              )}
              
              {!loading && stats.icuOccupancyRate <= 85 && stats.occupancyRate > 80 && (
                <div className="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
                  <p className="text-xs font-bold text-amber-900">High Occupancy</p>
                  <p className="text-[10px] text-amber-700 mt-1">Hospital at {stats.occupancyRate}% capacity. Monitor ER admissions.</p>
                </div>
              )}

              {!loading && stats.occupancyRate <= 80 && stats.icuOccupancyRate <= 85 && (
                <div className="p-3 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
                  <p className="text-xs font-bold text-blue-900">System Nominal</p>
                  <p className="text-[10px] text-blue-700 mt-1">All systems operating normally.</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-900 rounded-xl shadow-lg p-6 flex flex-col text-white flex-1">
            <h3 className="font-bold text-sm mb-4">Current Distribution</h3>
            <div className="flex-1 relative flex items-center justify-center min-h-[160px]">
               <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    <Cell fill="#3b82f6" />
                    <Cell fill="#334155" />
                  </Pie>
                  <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', background: '#1e293b', color: '#fff', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)' }} itemStyle={{ color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                <span className="text-2xl font-bold">{stats.occupancyRate}%</span>
                <span className="text-[10px] text-slate-400 uppercase font-medium mt-1">Occupied</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
