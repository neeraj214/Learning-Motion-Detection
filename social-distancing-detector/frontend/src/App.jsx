import React from 'react';
import useStatus from './hooks/useStatus';
import StatusBanner from './components/StatusBanner';
import StatsPanel from './components/StatsPanel';
import VideoFeed from './components/VideoFeed';
import ConnectionGuard from './components/ConnectionGuard';

export default function App() {
  const data = useStatus();

  // Determine dot color logic
  let dotColor = "bg-green-500";
  if (data.alarm_state === "warning") dotColor = "bg-yellow-400";
  else if (data.alarm_state === "alarm") dotColor = "bg-red-500 animate-pulse";

  return (
    <ConnectionGuard fps={data.fps}>
      <div className="min-h-screen bg-gray-950 text-white flex flex-col font-sans">
      
      {/* 1. Header */}
      <header className="bg-gray-900/80 backdrop-blur border-b border-gray-800 px-6 py-3 flex items-center gap-3 sticky top-0 z-10 shadow-sm">
        <div className={`w-3 h-3 rounded-full ${dotColor}`}></div>
        <h1 className="font-semibold text-white text-lg">Social Distancing Detector</h1>
        <span className="ml-2 text-gray-500 text-sm hidden sm:inline">— Real-time MOG2 Detection</span>
        
        <div className="ml-auto flex items-center gap-2">
          <span className="bg-gray-800 text-gray-400 text-xs px-3 py-1 rounded-full whitespace-nowrap">
            FastAPI + OpenCV
          </span>
        </div>
      </header>

      {/* 2. Status Banner */}
      <StatusBanner alarm_state={data.alarm_state} violation_pairs={data.violation_pairs} />

      {/* 3. Main Content */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        
        {/* Left + Center */}
        <section className="lg:col-span-2 flex flex-col">
          <VideoFeed alarm_state={data.alarm_state} />

          {/* Violation List Panel */}
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-4 mt-6 shadow-sm">
            <h2 className="text-white font-semibold text-sm mb-3">Violation Pairs</h2>
            
            {!data.violation_pairs || data.violation_pairs.length === 0 ? (
              <p className="text-gray-600 text-sm text-center py-4">No violations detected</p>
            ) : (
              <div className="flex flex-col max-h-48 overflow-y-auto pr-2">
                {data.violation_pairs.map((pair, idx) => (
                  <div 
                    key={idx} 
                    className="bg-red-950/50 border border-red-900 rounded-lg px-4 py-2 mb-2 text-red-300 text-sm font-mono flex items-center shadow-sm"
                  >
                    <span>Person {pair[0]}</span>
                    <span className="mx-4 text-red-500/50">↔</span>
                    <span>Person {pair[1]}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Right Column */}
        <section className="lg:col-span-1">
          <StatsPanel 
            fps={data.fps}
            active_ids={data.active_ids}
            violation_pairs={data.violation_pairs}
            alarm_state={data.alarm_state}
          />
        </section>

      </main>

      {/* 4. Footer */}
      <footer className="bg-gray-900 border-t border-gray-800 px-6 py-4 text-center text-xs text-gray-600">
        neeraj214 · Social Distancing Detector · MOG2 Background Subtraction
      </footer>
      
      </div>
    </ConnectionGuard>
  );
}
