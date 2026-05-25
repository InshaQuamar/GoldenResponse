import { useState, useEffect } from 'react';
import { BedIcon, Search, UserPlus, LogOut, Loader2 } from 'lucide-react';
import { socket } from '../App';

type Bed = {
  _id: string;
  bed_number: string;
  bed_type: 'ICU' | 'GENERAL' | 'EMERGENCY';
  occupancy_status: 'VACANT' | 'OCCUPIED';
  ward: string;
  updatedAt: string;
};

export default function WardManagement() {
  const [beds, setBeds] = useState<Bed[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchBeds();

    socket.on('bedUpdated', (updatedBed: Bed) => {
      setBeds(prev => prev.map(b => b._id === updatedBed._id ? updatedBed : b));
    });

    return () => {
      socket.off('bedUpdated');
    };
  }, []);

  const fetchBeds = async () => {
    try {
      const res = await fetch('/api/beds');
      const data = await res.json();
      setBeds(data);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const handleAllocate = async (id: string) => {
    setActionLoading(id);
    try {
      await fetch(`/api/beds/${id}/allocate`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDischarge = async (id: string) => {
    setActionLoading(id);
    try {
      await fetch(`/api/beds/${id}/discharge`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const filteredBeds = beds.filter(b => {
    if (filter === 'ALL') return true;
    if (filter === 'ICU') return b.bed_type === 'ICU';
    if (filter === 'GENERAL') return b.bed_type === 'GENERAL';
    if (filter === 'EMERGENCY') return b.bed_type === 'EMERGENCY';
    if (filter === 'VACANT') return b.occupancy_status === 'VACANT';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="hidden">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Bed Allocation</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time status of hospital beds across all wards.</p>
        </div>
        <div className="flex w-full sm:w-auto space-x-2">
           <div className="relative w-full sm:w-auto">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search bed number..." 
                className="pl-9 pr-4 py-2 bg-slate-50 border-transparent rounded-full text-sm w-full focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {['ALL', 'VACANT', 'ICU', 'GENERAL', 'EMERGENCY'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors border ${
              filter === f 
                ? 'bg-blue-600 text-white border-blue-600 shadow-sm' 
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-800'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredBeds.map(bed => (
            <div 
              key={bed._id} 
              className={`rounded-xl border p-5 transition-all
                ${bed.occupancy_status === 'OCCUPIED' 
                  ? 'bg-white border-slate-200 shadow-sm' 
                  : 'bg-white border-green-200 shadow-sm'}
              `}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg mr-3 ${bed.occupancy_status === 'OCCUPIED' ? 'bg-slate-100 text-slate-500' : 'bg-green-100 text-green-600'}`}>
                    <BedIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{bed.bed_number}</h3>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">{bed.ward}</span>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase ${
                  bed.bed_type === 'ICU' ? 'bg-blue-100 text-blue-700' :
                  bed.bed_type === 'EMERGENCY' ? 'bg-red-100 text-red-700' :
                  'bg-slate-100 text-slate-700'
                }`}>
                  {bed.bed_type}
                </span>
              </div>
              
              <div className="mt-6 flex gap-2">
                {bed.occupancy_status === 'VACANT' ? (
                  <button 
                    disabled={actionLoading === bed._id}
                    onClick={() => handleAllocate(bed._id)}
                    className="flex-1 flex items-center justify-center py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    {actionLoading === bed._id ? <Loader2 className="w-4 h-4 animate-spin" /> : <><UserPlus className="w-4 h-4 mr-2" /> Admit</>}
                  </button>
                ) : (
                  <button 
                    disabled={actionLoading === bed._id}
                    onClick={() => handleDischarge(bed._id)}
                    className="flex-1 flex items-center justify-center py-2 bg-white border border-slate-200 hover:bg-slate-50 hover:text-red-600 text-slate-700 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    {actionLoading === bed._id ? <Loader2 className="w-4 h-4 animate-spin" /> : <><LogOut className="w-4 h-4 mr-2" /> Discharge</>}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filteredBeds.length === 0 && (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-white">
          <BedIcon className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900">No beds found</h3>
          <p className="text-slate-500 text-sm">Adjust your filters to see more results.</p>
        </div>
      )}
    </div>
  );
}
