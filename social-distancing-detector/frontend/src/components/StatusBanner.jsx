export default function StatusBanner({ alarm_state, violation_pairs = [] }) {
  let bgColorClass = "bg-green-600";
  let pulseClass = "";

  if (alarm_state === "warning") {
    bgColorClass = "bg-yellow-500";
  } else if (alarm_state === "alarm") {
    bgColorClass = "bg-red-600";
    pulseClass = "animate-pulse";
  }

  return (
    <div className={`w-full transition-colors duration-300 ${bgColorClass} ${pulseClass}`}>
      <div className="flex items-center justify-center gap-3 py-3 shadow-md">
        <div className="w-3 h-3 rounded-full bg-white opacity-90"></div>
        <span className="font-bold text-white text-lg tracking-wider">
          {alarm_state.toUpperCase()}
        </span>
        {alarm_state !== "safe" && (
          <span className="text-white text-sm font-medium">
            — {violation_pairs.length} pair(s) violating distance
          </span>
        )}
      </div>
    </div>
  );
}
