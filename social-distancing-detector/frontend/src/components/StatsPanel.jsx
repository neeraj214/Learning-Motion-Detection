import React from 'react';

export default function StatsPanel({ fps, active_ids = [], violation_pairs = [], alarm_state }) {
  const peopleCount = active_ids.length;
  const violationCount = violation_pairs.length;
  const roundedFps = Math.round(fps || 0);

  // Status color logic
  let statusColor = "text-green-400";
  if (alarm_state === "warning") statusColor = "text-yellow-400";
  else if (alarm_state === "alarm") statusColor = "text-red-400";

  // FPS color logic
  let fpsColor = "text-red-400";
  if (roundedFps >= 15) fpsColor = "text-green-400";
  else if (roundedFps >= 8) fpsColor = "text-yellow-400";

  return (
    <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
      <h2 className="text-white font-semibold text-base mb-4">Live Stats</h2>
      
      <div className="grid grid-cols-2 gap-3">
        {/* Tile 1: People */}
        <div className="bg-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{peopleCount}</span>
          <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">People</span>
        </div>

        {/* Tile 2: Violations */}
        <div className="bg-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${violationCount > 0 ? 'text-red-400' : 'text-white'}`}>
            {violationCount}
          </span>
          <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">Violations</span>
        </div>

        {/* Tile 3: FPS */}
        <div className="bg-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${fpsColor}`}>{roundedFps}</span>
          <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">FPS</span>
        </div>

        {/* Tile 4: Status */}
        <div className="bg-gray-800 rounded-xl p-4 flex flex-col items-center justify-center">
          <span className={`text-sm font-semibold ${statusColor}`}>
            {(alarm_state || "safe").toUpperCase()}
          </span>
          <span className="text-xs text-gray-400 uppercase tracking-wider mt-1">Status</span>
        </div>
      </div>

      <h3 className="text-gray-400 text-xs uppercase mt-4 mb-2">Active IDs</h3>
      <div>
        {peopleCount > 0 ? (
          active_ids.map(id => (
            <span key={id} className="inline-block bg-gray-700 text-gray-200 text-xs rounded-full px-2 py-0.5 mr-1 mb-1 font-mono">
              {id}
            </span>
          ))
        ) : (
          <span className="text-gray-600 text-xs">No people detected</span>
        )}
      </div>
    </div>
  );
}
