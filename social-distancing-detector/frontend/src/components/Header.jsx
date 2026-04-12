import React from 'react';

const Header = ({ status = 'safe' }) => {
  const isAlarm = status === 'alarm';
  
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800/50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white leading-none">SOCIAL VIGILANCE AI</h1>
            <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em] font-medium mt-1">Live Monitoring System</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-zinc-900/50 px-3 py-1.5 rounded-full border border-zinc-800/50">
            <div className={`w-2 h-2 rounded-full ${isAlarm ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}></div>
            <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              {status === 'safe' ? 'System Normal' : status === 'warning' ? 'Alert Active' : 'Emergency State'}
            </span>
          </div>
          <div className="text-zinc-500 text-xs font-medium tabular-nums">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
