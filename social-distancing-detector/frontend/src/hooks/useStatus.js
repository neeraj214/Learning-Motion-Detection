import { useState, useEffect } from 'react';
import { STATUS_URL } from '../config';

export default function useStatus() {
  const [status, setStatus] = useState({
    fps: 0,
    active_ids: [],
    violation_pairs: [],
    alarm_state: "safe",
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(STATUS_URL);
        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        }
      } catch (error) {
        // Silently keep last known state on error
      }
    };

    // Initial fetch
    fetchStatus();

    const intervalId = setInterval(fetchStatus, 500);

    return () => {
      clearInterval(intervalId);
    };
  }, []);

  return status;
}
