import React, { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isToday } from 'date-fns';
import './AiSchedule.css';
import { Card, CardContent, Typography, Chip, Stack } from '@mui/material';



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
    summary: string;
    start: string;
    end: string;
    location: string | null;
    description?: string;
    type?: string;
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
  const [applying, setApplying] = useState<boolean>(false);
  const [applyMessage, setApplyMessage] = useState<string>("");

  // Base URL for API from environment
  const API_BASE_URL = (import.meta as any).env.VITE_API_URL ?? "http://egoai.duckdns.org:8000";

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
      console.log("Fetching calendar from:", `${API_BASE_URL}/api/v1/calendar/get_tasks`);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/calendar/get_tasks`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Include cookies for authentication
      });

      console.log("Calendar response status:", response.status);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in.");
        }
        throw new Error(`Failed to fetch calendar: ${response.status} ${response.statusText}`);
      }

      const rawData = await response.json();
      console.log("Raw calendar data:", rawData);
      
      // Convert datetime strings to Date objects to match CalendarEvent interface
      const data: CalendarEvent[] = rawData.map((event: any) => ({
        id: event.id,
        title: event.title,
        start: new Date(event.start_time),
        end: new Date(event.end_time),
        type: event.type as 'focus' | 'tasks' | 'target' | 'other',
        description: event.description,
        location: event.location,
      }));
      
      console.log("Processed calendar events:", data);
      setEvents(data);
      
      // Show a user-friendly message if no events are found
      if (data.length === 0) {
        setError("No calendar events found. Please add some events to your calendar first.");
      } else {
        setError(""); // Clear any previous errors
      }
    } catch (err: any) {
      console.error("Error fetching full calendar:", err);
      setError(`Unable to load calendar events: ${err.message}`);
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
      // Check if we have events to reschedule
      if (events.length === 0) {
        setError("No events found to reschedule. Please add some events to your calendar first.");
        return;
      }

      // Prepare the calendar data to send to the API
      const calendar = events.map((e: CalendarEvent) => ({
        summary: e.title,
        start: e.start.toISOString(),
        end: e.end.toISOString(),
        location: e.location || ""
      }));

      console.log("Sending calendar data to rescheduler:", calendar);

      // Make the API call to fetch recommendations
      const response = await fetch("http://egoai.duckdns.org:8001/reschedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ calendar })
      });

      console.log("Rescheduler response status:", response.status);

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
      console.log("Rescheduler response data:", data);
      console.log("New calendar events:", data.new_calendar);
      
      // Debug each event structure
      if (data.new_calendar) {
        data.new_calendar.forEach((item, index) => {
          console.log(`Event ${index}:`, item);
          console.log(`Event ${index} structure:`, {
            hasEvent: !!item.event,
            eventKeys: item.event ? Object.keys(item.event) : 'no event object',
            summary: item.event?.summary,
            start: item.event?.start,
            end: item.event?.end,
            location: item.event?.location,
            type: item.event?.type
          });
        });
      }

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

  // Применяет оптимизированный график к календарю через API
  const applyOptimized = async () => {
    if (!recCalendar) return;
    setApplying(true);
    setApplyMessage("");
    try {
      await Promise.all(recCalendar.map(async item => {
        const e = item.event;
        const payload = {
          title: e.summary,
          description: e.description || '',
          start_time: e.start,
          end_time: e.end,
          location: e.location || ''
        };
        // Ищем существующее событие по заголовку
        const existing = events.find(ev => ev.title === e.summary);
        const url = existing
          ? `${API_BASE_URL}/api/v1/calendar/update_task/${existing.id}`
          : `${API_BASE_URL}/api/v1/calendar/set_task`;
        const method = existing ? 'PUT' : 'POST';
        await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          credentials: 'include'
        });
      }));
      setApplyMessage('Календарь успешно обновлен.');
      fetchFullCalendar();
    } catch (err: any) {
      console.error('Apply Error:', err);
      setApplyMessage('Ошибка при применении: ' + err.message);
    } finally {
      setApplying(false);
    }
  };

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
            {loading ? "🤖 Analyzing..." : "Get Recommendations"}
          </button>
        </div>
        <div className="recs-content">
          {loading && (
            <div className="status-card">
              <h2>🤖 AI is thinking...</h2>
              <p className="loading-text">Analyzing your schedule and generating recommendations...</p>
            </div>
          )}
          
          {!loading && (
            <>
              <div className="status-card">
                <h2>📅 Your Calendar</h2>
                <p>{events.length} events loaded</p>
                {events.length > 0 && <p>Recent events:</p>}
              </div>
          
          {events.length > 0 && (
            <Stack spacing={2} sx={{ padding: 2 }}>
              {events.slice(0, 3).map(event => (
                <Card key={event.id} variant="outlined" sx={{ backdropFilter: 'blur(8px)', bgcolor: 'rgba(255,255,255,0.7)' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="h6">{event.title}</Typography>
                      <Chip label={event.type} color="success"/>
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {format(event.start, 'HH:mm')} – {format(event.end, 'HH:mm')}
                    </Typography>
                    {event.location && (
                      <Typography variant="body2" color="text.secondary">
                        📍 {event.location}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
          
          {error && (
            <div className="status-card">
              <h2>⚠️ Error</h2>
              <p className="error-text">{error}</p>
            </div>
          )}
          
          {recSuggestion && (
            <div className="suggestion-header">
              <h2>🤖 AI Recommendation</h2>
            </div>
          )}
          
          {recSuggestion && (
            <div className="status-card">
              <p>{recSuggestion}</p>
            </div>
          )}
          
          {recCalendar && recCalendar.length > 0 && (
            <>
              <div className="suggestion-header">
                <h2>✨ Optimized Schedule</h2>
              </div>
              <div className="optimized-events">
                {recCalendar.map((item, index) => {
                  // Access the event data safely
                  const eventData = item.event;
                  const title = eventData?.summary || 'Untitled Event';
                  const startTime = eventData?.start || 'No start time';
                  const endTime = eventData?.end || 'No end time';
                  const location = eventData?.location || '';
                  const type = eventData?.type || '';
                  
                  // Format the times for better display
                  const formatTime = (timeStr: string) => {
                    try {
                      if (timeStr && timeStr !== 'No start time' && timeStr !== 'No end time') {
                        // Handle different time formats
                        let dateTime: Date;
                        if (timeStr.includes('T')) {
                          // ISO format like "2025-07-18T13:00"
                          dateTime = new Date(timeStr);
                        } else {
                          // Just time like "13:00"
                          dateTime = new Date(`2025-07-18T${timeStr}`);
                        }
                        
                        if (!isNaN(dateTime.getTime())) {
                          return dateTime.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit',
                            hour12: false 
                          });
                        }
                      }
                      return timeStr;
                    } catch {
                      return timeStr;
                    }
                  };

                  // Get type icon
                  const getTypeIcon = (type: string) => {
                    switch (type) {
                      case 'meeting': return '👥';
                      case 'call': return '📞';
                      case 'personal': return '🏠';
                      case 'focus time': return '🎯';
                      case 'other work': return '💼';
                      default: return '📝';
                    }
                  };
                  
                  return (
                    <div key={`${title}-${index}`} className="event-card">
                      <div className="event-header">
                        <h3 className="event-title">{title}</h3>
                        <span className="event-type-badge">
                          {getTypeIcon(type)} {type}
                        </span>
                      </div>
                      <div className="event-details">
                        <div className="event-time">
                          🕐 {formatTime(startTime)} - {formatTime(endTime)}
                        </div>
                        {location && location !== 'Unknown location' && (
                          <div className="event-location">
                            📍 {location}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              {/* Кнопка применения изменений в календарь */}
              <div className="recs-footer">
                <button className="recs-btn" onClick={applyOptimized} disabled={applying}>
                  {applying ? 'Применяется...' : 'Применить в календарь'}
                </button>
                {applyMessage && <p className="apply-msg">{applyMessage}</p>}
              </div>
            </>
          )}
          
          {recCalendar && recCalendar.length === 0 && (
            <div className="status-card">
              <h2>📅 No Changes Needed</h2>
              <p>Your schedule is already optimized!</p>
            </div>
          )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export { AiSchedule };
export default AiSchedule;