import React from 'react';

const StatusBanner = ({ alarm_state = 'safe', violation_count = 0 }) => {
  let bgColorClass = 'bg-green-600';
  let extraClasses = '';

  if (alarm_state === 'warning') {
    bgColorClass = 'bg-yellow-500';
  } else if (alarm_state === 'alarm') {
    bgColorClass = 'bg-red-600';
    extraClasses = 'animate-pulse';
  }

  const containerClasses = `w-full py-4 px-6 text-center text-white flex items-center justify-center transition-colors duration-300 ${bgColorClass} ${extraClasses}`;

  return (
    <div className={containerClasses}>
      <span className="font-bold text-lg uppercase tracking-wider">{alarm_state}</span>
      {alarm_state !== 'safe' && (
        <span className="ml-2 text-lg font-medium opacity-90">
          — {violation_count} pair(s) too close
        </span>
      )}
    </div>
  );
};

export default StatusBanner;
