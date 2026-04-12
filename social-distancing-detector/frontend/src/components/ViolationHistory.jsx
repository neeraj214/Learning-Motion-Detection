import React, { useState, useEffect } from 'react';

const ViolationHistory = ({ currentViolationCount = 0, alarmState = 'safe' }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (currentViolationCount > 0) {
      const newEvent = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        count: currentViolationCount,
        severity: alarmState
      };
      
      setHistory(prev => [newEvent, ...prev].slice(0, 10)); // Keep last 10
    }
  }, [currentViolationCount, alarmState]);

  return (
    <div className="glass-card rounded-xl p-5 h-full flex flex-col">
      <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-4 flex items-center justify-between">
        Live Activity Log
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
      </h3>
      
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
        {history.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-2 py-10">
            <svg className="w-8 h-8 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-xs font-medium">No violations detected</p>
          </div>
        ) : (
          history.map((item) => (
            <div key={item.id} className="glass-tile flex items-center justify-between group">
              <div className="flex flex-col">
                <span className="text-[10px] text-zinc-500 font-bold tabular-nums">{item.timestamp}</span>
                <span className="text-sm font-semibold text-zinc-200">
                  {item.count} pair{item.count > 1 ? 's' : ''} detected
                </span>
              </div>
              <div className={`px-2 py-1 rounded text-[10px] font-black uppercase ${
                item.severity === 'alarm' ? 'bg-red-500/20 text-red-500' : 'bg-yellow-500/20 text-yellow-500'
              }`}>
                {item.severity}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ViolationHistory;
