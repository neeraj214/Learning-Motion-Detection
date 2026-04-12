import { useState, useEffect } from 'react';
import { EVENTS_URL } from '../config.js';

const useSSE = () => {
  const [data, setData] = useState({
    alarm_state: "safe",
    total_people: 0,
    violation_count: 0,
    total_violations: 0,
  });

  useEffect(() => {
    const source = new EventSource(EVENTS_URL);

    source.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    source.onerror = (err) => {
      console.error('SSE Error:', err);
    };

    return () => {
      source.close();
    };
  }, []);

  return data;
};

export default useSSE;
