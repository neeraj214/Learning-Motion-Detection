import React from 'react';

export default function ConnectionGuard({ fps, children }) {
  if (fps === 0) {
    return (
      <div className="fixed inset-0 bg-gray-950/90 flex flex-col items-center justify-center z-50">
        <div className="w-16 h-16 rounded-full bg-red-900/50 flex items-center justify-center mb-4">
          <span className="text-red-400 text-3xl">✕</span>
        </div>
        <h2 className="text-white font-bold text-xl mb-2">Backend Unreachable</h2>
        <p className="text-gray-400 text-sm text-center max-w-xs">
          Make sure the FastAPI server is running on port 8000
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-6 bg-gray-800 hover:bg-gray-700 text-white text-sm px-5 py-2 rounded-lg cursor-pointer border border-gray-700 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return children;
}
