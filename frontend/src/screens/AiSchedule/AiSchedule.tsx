import React, { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isToday } from 'date-fns';
// import { fetchEvents } from '@/utils/calendarApi';
import './AiSchedule.css';
import { gapi } from 'gapi-script';



export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'focus' | 'tasks' | 'target' | 'other';
  description?: string;
  location?: string;
}

export interface RescheduleEvent {
  event: {
    title: string;
    description: string;
    start_time: string;
    end_time: string;
    all_day: boolean;
    location: string;
    type: string;
  };
}

export interface RescheduleResponse {
  suggestion: string;
  new_calendar?: RescheduleEvent[];
}


const AiSchedule: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events,    setEvents] = useState<CalendarEvent[]>([]);
  const [recSuggestion, setRecSuggestion] = useState<string>("");
  const [recCalendar, setRecCalendar] = useState<RescheduleEvent[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const goToPreviousWeek = () => setCurrentDate(subWeeks(currentDate, 1));
  const goToNextWeek = () => setCurrentDate(addWeeks(currentDate, 1));

  const getWeekDays = () => {
    const start = startOfWeek(currentDate);
    return Array.from({ length: 7 }, (_, i) => ({
      date: addDays(start, i + 1),
      id: `day-${i}` // Unique key for each day
    }));
  };

  useEffect(() => {
    // Here you can fetch and setEvents if needed
  }, [currentDate]);

  const fetchFullCalendar = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/v1/calendar/get_tasks", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch the full calendar");
      }

      const data: CalendarEvent[] = await response.json();
      setEvents(data);
    } catch (err: any) {
      console.error("Error fetching full calendar:", err);
      setError("Unable to load calendar events.");
    }
  };

  useEffect(() => {
    fetchFullCalendar();
  }, []);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError("");
    setRecSuggestion("");
    setRecCalendar(null);

    try {
      // Prepare the calendar data to send to the API
      const calendar = events.map((e: CalendarEvent) => ({
        summary: e.title,
        start: e.start.toISOString(),
        end: e.end.toISOString(),
        location: e.location || ""
      }));

      // Make the API call to fetch recommendations
      const response = await fetch("http://localhost:8001/reschedule/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ calendar })
      });

      // Check if the response is not OK
      if (!response.ok) {
        const errorText = await response.text();
        console.error("API Response Error:", response.status, errorText);

        if (response.status === 500) {
          throw new Error("Server error: Unable to process the request. Please try again later.");
        } else if (response.status === 400) {
          throw new Error("Bad request: Please check the input data.");
        } else {
          throw new Error(`Unexpected error: ${response.statusText}`);
        }
      }

      // Parse the response JSON
      const data: RescheduleResponse = await response.json();

      // Update state with the fetched data
      setRecSuggestion(data.suggestion || "No suggestion available");
      setRecCalendar(data.new_calendar || null);
    } catch (err: any) {
      // Log the error for debugging
      console.error("Fetch Recommendations Error:", err);
      setError(err.message || "Unknown error");
    } finally {
      // Ensure loading state is reset
      setLoading(false);
    }
  }, [events]);

  return (
    <div className="ai-schedule-container">
      <div className="weeks-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Week</h2>
          <div className="ai-schedule-nav">
            <button className="nav-btn" onClick={goToPreviousWeek}>←</button>
            <button className="nav-btn" onClick={goToNextWeek}>→</button>
            <span className="month-year">{format(currentDate, 'MMMM yyyy')}</span>
          </div>
        </div>
        <div className="sidebar-content">
          {getWeekDays().map(({ date, id }) => (
            <button 
              key={id} 
              className={`day-btn ${isToday(date) ? 'today' : ''}`}
            >
              <div>{format(date, 'EEEE, d')}</div>
            </button>
          ))}
        </div>
      </div>
      <div className="recs-section">
        <div className="recs-header">
          <h1 className="recs-title">Recommendations on tasks</h1>
          <button className="recs-btn" onClick={fetchRecommendations} disabled={loading}>
            {loading ? "Loading..." : "Get Recommendations"}
          </button>
        </div>
        <div className="recs-content">
          {error && <div className="recs-error">{error}</div>}
          {recSuggestion && <div className="recs-suggestion">{recSuggestion}</div>}
          {recCalendar && (
            <div className="recs-calendar">
              <h3>Optimized Calendar:</h3>
              <ul>
                {recCalendar.map((item) => (
                  <li key={item.event.title + item.event.start_time}>
                    <b>{item.event.title}</b> — {item.event.start_time} to {item.event.end_time} @ {item.event.location} <i>({item.event.type})</i>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export { AiSchedule };
export default AiSchedule;