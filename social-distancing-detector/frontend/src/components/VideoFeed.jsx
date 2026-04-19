import React from 'react';
import { VIDEO_FEED_URL } from '../config';

export default function VideoFeed({ alarm_state }) {
  let borderColor = "border-green-600";
  if (alarm_state === "warning") {
    borderColor = "border-yellow-500";
  } else if (alarm_state === "alarm") {
    borderColor = "border-red-600";
  }

  return (
    <div className={`relative rounded-2xl overflow-hidden border-2 transition-colors duration-300 ${borderColor}`}>
      <img
        src={VIDEO_FEED_URL}
        alt="Live feed"
        className="w-full h-auto block"
      />
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-4 py-3 flex items-center justify-between">
        <div className="flex items-center">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse inline-block mr-2"></span>
          <span className="text-white text-xs font-mono font-bold">LIVE</span>
        </div>
        <div>
          <span className="text-gray-400 text-xs">MOG2 Background Subtraction</span>
        </div>
      </div>
    </div>
  );
}
