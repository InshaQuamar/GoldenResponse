import { useState } from 'react';
import { Users, Search, Filter, ShieldPlus, Clock } from 'lucide-react';

const mockStaff = [
  { id: '1', name: 'Dr. Jane Doe', role: 'Lead Administrator', department: 'Emergency', status: 'ON_SHIFT', shift: '08:00 - 16:00' },
  { id: '2', name: 'Dr. John Smith', role: 'Cardiologist', department: 'ICU', status: 'OFF_SHIFT', shift: '16:00 - 00:00' },
  { id: '3', name: 'Sarah Connor', role: 'Head Nurse', department: 'ICU', status: 'ON_SHIFT', shift: '08:00 - 20:00' },
  { id: '4', name: 'Michael Chang', role: 'Nurse Practitioner', department: 'General', status: 'ON_SHIFT', shift: '08:00 - 16:00' },
  { id: '5', name: 'Emily Davis', role: 'Surgeon', department: 'Surgery', status: 'ON_CALL', shift: '24h' },
  { id: '6', name: 'Robert Wilson', role: 'Anesthesiologist', department: 'Surgery', status: 'OFF_SHIFT', shift: 'Tomorrow 08:00' },
];

export default function StaffManagement() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredStaff = mockStaff.filter(s => 
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    s.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Staff & Shifts</h1>
          <p className="text-slate-500 text-sm mt-1">Manage hospital personnel roster and schedules.</p>
        </div>
        <div className="flex w-full sm:w-auto space-x-2">
           <div className="relative w-full sm:w-auto">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search personnel..." 
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

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Personnel</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Department</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Status</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs">Current Shift</th>
                <th className="px-6 py-4 font-bold text-slate-700 uppercase tracking-wider text-xs text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStaff.map((staff) => (
                <tr key={staff.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                        {staff.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                      </div>
                      <div className="ml-4">
                        <div className="font-bold text-slate-900">{staff.name}</div>
                        <div className="text-slate-500 text-xs">{staff.role}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">
                      {staff.department}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      staff.status === 'ON_SHIFT' ? 'bg-green-100 text-green-700' : 
                      staff.status === 'ON_CALL' ? 'bg-amber-100 text-amber-700' : 
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {staff.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center text-slate-600 font-medium">
                      <Clock className="w-4 h-4 mr-2 text-slate-400" />
                      {staff.shift}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-blue-600 hover:text-blue-900 font-semibold text-sm">Update</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredStaff.length === 0 && (
            <div className="text-center py-12 px-6">
              <Users className="mx-auto h-12 w-12 text-slate-300" />
              <h3 className="mt-2 text-sm font-semibold text-slate-900">No personnel found</h3>
              <p className="mt-1 text-sm text-slate-500">Try adjusting your search query.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
