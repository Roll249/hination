import React from 'react';

function DistrictSelector({ districts, selectedId, onSelect }) {
  // Calculate risk level for a district
  const getRiskLevel = (districtData) => {
    let risk = 0;
    const c = districtData.current;
    
    if (c.rainfall > 5) risk += 3;
    else if (c.rainfall > 2) risk += 2;
    else if (c.rainfall > 0.5) risk += 1;
    
    if (c.humidity > 95) risk += 2;
    else if (c.humidity > 85) risk += 1;
    
    if (c.temp < 5) risk += 3;
    else if (c.temp < 10) risk += 2;
    else if (c.temp < 15) risk += 1;

    if (risk >= 5) return { level: 'severe', color: 'bg-red-500', text: 'text-red-400', label: 'Nguy hiểm' };
    if (risk >= 3) return { level: 'high', color: 'bg-orange-500', text: 'text-orange-400', label: 'Cao' };
    if (risk >= 2) return { level: 'moderate', color: 'bg-yellow-500', text: 'text-yellow-400', label: 'TB' };
    return { level: 'low', color: 'bg-emerald-500', text: 'text-emerald-400', label: 'Thấp' };
  };

  return (
    <div className="card">
      <div className="p-4 border-b border-slate-700/50">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span>📍</span> Chọn khu vực
        </h3>
      </div>
      
      <div className="p-2 max-h-80 overflow-y-auto">
        {Object.entries(districts).map(([id, data]) => {
          const risk = getRiskLevel(data);
          const isSelected = id === selectedId;
          
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`w-full p-3 rounded-lg text-left transition-all mb-1 ${
                isSelected 
                  ? 'bg-blue-500/20 border border-blue-500/50' 
                  : 'hover:bg-slate-700/50 border border-transparent'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${risk.color}`}></span>
                    <span className={`font-medium ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                      {data.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                    <span>{data.current.temp}°C</span>
                    <span>{data.current.humidity}%</span>
                    <span>{data.current.rainfall}mm</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${risk.text} ${risk.color}/20`}>
                    {risk.label}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-slate-700/50">
        <div className="text-xs text-slate-500 mb-2">Mức độ rủi ro:</div>
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            <span className="text-slate-400">Thấp</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-slate-400">TB</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-slate-400">Cao</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-slate-400">Nguy hiểm</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DistrictSelector;
