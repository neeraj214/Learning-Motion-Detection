import React from 'react';
import useSSE from './hooks/useSSE';
import { VIDEO_FEED_URL } from './config';
import Header from './components/Header';
import StatusBanner from './components/StatusBanner';
import StatsPanel from './components/StatsPanel';
import ViolationHistory from './components/ViolationHistory';

function App() {
  const { alarm_state, total_people, violation_count, total_violations } = useSSE();

  return (
    <div className="min-h-screen bg-zinc-950 text-slate-200 selection:bg-blue-500/30">
      <Header status={alarm_state} />

      <main className="max-w-7xl mx-auto pt-24 pb-12 px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Video Feed */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="relative group overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl">
              {/* Overlay Badges */}
              <div className="absolute top-4 left-4 z-10 flex gap-2">
                <div className="bg-black/60 backdrop-blur-md border border-white/10 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                  Live Feed
                </div>
              </div>

              {/* MJPEG Stream */}
              <div className="aspect-video bg-zinc-950 flex items-center justify-center overflow-hidden">
                <img 
                  src={VIDEO_FEED_URL} 
                  alt="AI Video Analytics" 
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "https://via.placeholder.com/1280x720/09090b/3f3f46?text=Waiting+for+Stream...";
                  }}
                />
              </div>

              {/* Integrated Status Banner */}
              <div className="absolute bottom-0 left-0 right-0">
                 <StatusBanner 
                    alarm_state={alarm_state} 
                    violation_count={violation_count} 
                 />
              </div>
            </div>

            {/* Quick Action / Info Bar */}
            <div className="glass-card rounded-xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-zinc-800 rounded-lg">
                  <svg className="w-5 h-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm text-zinc-400 leading-snug">
                  AI-driven monitoring is active. <br/>
                  <span className="text-zinc-500 text-xs">Distance thresholds are enforced at 60px (approx. 2m).</span>
                </p>
              </div>
              <button 
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-xs font-bold uppercase tracking-wider rounded-lg transition-colors border border-zinc-700"
              >
                Reset Stream
              </button>
            </div>
          </div>

          {/* Right Column: Analytics & History */}
          <div className="lg:col-span-4 flex flex-col gap-8">
            <section>
              <h2 className="text-xs font-black text-zinc-500 uppercase tracking-[0.2em] mb-4 pl-1">Metrics Dashboard</h2>
              <StatsPanel 
                total_people={total_people}
                violation_count={violation_count}
                total_violations={total_violations}
                alarm_state={alarm_state}
              />
            </section>

            <section className="flex-1">
              <ViolationHistory 
                currentViolationCount={violation_count}
                alarmState={alarm_state}
              />
            </section>
          </div>

        </div>
      </main>

      <footer className="border-t border-zinc-900 mt-12 py-8 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-zinc-600 text-[10px] font-medium tracking-wide">
            POWERED BY DEEP LEARNING & COMPUTER VISION
          </p>
          <div className="flex items-center gap-6">
            <span className="text-zinc-600 text-[10px] uppercase font-bold tracking-widest cursor-pointer hover:text-zinc-400 transition-colors">Documentation</span>
            <span className="text-zinc-600 text-[10px] uppercase font-bold tracking-widest cursor-pointer hover:text-zinc-400 transition-colors">API Status</span>
            <span className="text-zinc-600 text-[10px] uppercase font-bold tracking-widest cursor-pointer hover:text-zinc-400 transition-colors">V1.0.4</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
