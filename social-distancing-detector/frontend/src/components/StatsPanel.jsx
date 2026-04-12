import React from 'react';

const StatsPanel = ({ total_people = 0, violation_count = 0, total_violations = 0, alarm_state = 'safe' }) => {
  let statusColorClass = 'text-green-400';
  if (alarm_state === 'warning') statusColorClass = 'text-yellow-400';
  if (alarm_state === 'alarm') statusColorClass = 'text-red-400';

  const violationColor = violation_count > 0 ? 'text-red-500' : 'text-white';

  return (
    <div className="bg-gray-900 text-white rounded-xl p-4">
      <div className="grid grid-cols-2 gap-3">
        {/* Tile 1: People detected */}
        <div className="bg-gray-800 rounded-lg p-3 text-center flex flex-col justify-center">
          <div className="text-3xl font-bold">{total_people}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">People detected</div>
        </div>

        {/* Tile 2: Current violations */}
        <div className="bg-gray-800 rounded-lg p-3 text-center flex flex-col justify-center">
          <div className={`text-3xl font-bold ${violationColor}`}>{violation_count}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">Current violations</div>
        </div>

        {/* Tile 3: Total violations */}
        <div className="bg-gray-800 rounded-lg p-3 text-center flex flex-col justify-center">
          <div className="text-3xl font-bold">{total_violations}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">Total violations</div>
        </div>

        {/* Tile 4: Status */}
        <div className="bg-gray-800 rounded-lg p-3 text-center flex flex-col justify-center">
          <div className={`text-xl font-semibold uppercase ${statusColorClass}`}>{alarm_state}</div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">Status</div>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
