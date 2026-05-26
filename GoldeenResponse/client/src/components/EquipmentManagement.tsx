import { useState } from 'react';
import { Activity, Search, Filter, AlertTriangle, CheckCircle2, Stethoscope, Briefcase } from 'lucide-react';

const mockEquipments = [
  { id: 'EQ-001', name: 'Ventilator V-800', type: 'Life Support', location: 'ICU-A', status: 'IN_USE', condition: 'GOOD', nextMaintenance: '2023-11-15' },
  { id: 'EQ-002', name: 'Defibrillator D-20', type: 'Emergency', location: 'ER-Bay-2', status: 'STANDBY', condition: 'GOOD', nextMaintenance: '2023-10-20' },
  { id: 'EQ-003', name: 'Portable X-Ray', type: 'Imaging', location: 'Radiology', status: 'MAINTENANCE', condition: 'REPAIR', nextMaintenance: '2023-09-01' },
  { id: 'EQ-004', name: 'Patient Monitor PM-1', type: 'Monitoring', location: 'ICU-B', status: 'IN_USE', condition: 'GOOD', nextMaintenance: '2024-01-10' },
  { id: 'EQ-005', name: 'Ventilator V-800', type: 'Life Support', location: 'Storage-East', status: 'STANDBY', condition: 'NOTICE', nextMaintenance: '2023-09-30' },
  { id: 'EQ-006', name: 'Infusion Pump', type: 'Therapeutics', location: 'Gen-01', status: 'IN_USE', condition: 'GOOD', nextMaintenance: '2023-12-05' },
];

export default function EquipmentManagement() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredEquipments = mockEquipments.filter(e => 
    e.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    e.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Equipments</h1>
          <p className="text-slate-500 text-sm mt-1">Track medical devices, location, and maintenance status.</p>
        </div>
        <div className="flex w-full sm:w-auto space-x-2">
           <div className="relative w-full sm:w-auto">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search by ID or name..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-full text-sm w-full focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
              />
            </div>
            <button className="flex items-center justify-center px-4 py-2 bg-white border border-slate-200 rounded-full text-sm font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm">
              <Filter className="w-4 h-4 mr-2" /> Filter
            </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="h-12 w-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center border border-blue-100">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-tight">Active Devices</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">342</h3>
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="h-12 w-12 bg-green-50 text-green-600 rounded-full flex items-center justify-center border border-green-100">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-tight">Standby</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">85</h3>
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="h-12 w-12 bg-orange-50 text-orange-600 rounded-full flex items-center justify-center border border-orange-100">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-tight">Needs Maintenance</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">14</h3>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Device</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Location</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Status</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Condition</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Next Maintenance</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEquipments.map((eq) => (
                <tr key={eq.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="h-8 w-8 flex-shrink-0 bg-slate-100 rounded flex items-center justify-center text-slate-500">
                        <Briefcase className="h-4 w-4" />
                      </div>
                      <div className="ml-3">
                        <div className="font-bold text-slate-900">{eq.name}</div>
                        <div className="text-slate-500 text-xs font-mono">{eq.id} &bull; {eq.type}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-900 font-semibold">{eq.location}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      eq.status === 'IN_USE' ? 'bg-blue-100 text-blue-700' : 
                      eq.status === 'STANDBY' ? 'bg-green-100 text-green-700' : 
                      'bg-orange-100 text-orange-700'
                    }`}>
                      {eq.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                     <div className="flex items-center space-x-1.5">
                       <span className={`w-2 h-2 rounded-full ${
                         eq.condition === 'GOOD' ? 'bg-green-500' : 
                         eq.condition === 'NOTICE' ? 'bg-amber-500' : 'bg-red-500'
                       }`}></span>
                       <span className="text-xs font-semibold text-slate-700">{eq.condition}</span>
                     </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-slate-600 font-medium">{new Date(eq.nextMaintenance).toLocaleDateString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-blue-600 hover:text-blue-900 font-semibold text-sm">Manage</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredEquipments.length === 0 && (
            <div className="text-center py-12 px-6">
              <Stethoscope className="mx-auto h-12 w-12 text-slate-300" />
              <h3 className="mt-2 text-sm font-semibold text-slate-900">No equipment found</h3>
              <p className="mt-1 text-sm text-slate-500">Try adjusting your search query.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
