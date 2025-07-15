import React, { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isToday } from 'date-fns';
// import { fetchEvents } from '@/utils/calendarApi';
import './AiSchedule.css';
import { gapi } from 'gapi-script';

interface CalendarDay {
    id: string;
    title: string;

}

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'focus' | 'tasks' | 'target' | 'other';
  description?: string;
}

export const AiSchedule: React.FC = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<CalendarEvent[]>([]);

    const goToPreviousWeek = () => setCurrentDate(subWeeks(currentDate, 1));
    const goToNextWeek = () => setCurrentDate(addWeeks(currentDate, 1));

    const getWeekDays = () => {
        const start = startOfWeek(currentDate);
        return Array.from({ length: 7 }, (_, i) => addDays(start, i+1));
    };


    const handleLogin = async () => {

        const start = startOfWeek(currentDate);
        const end = new Date(start);
        end.setDate(start.getDate() + 7);
        
        const res = await gapi.client.calendar.events.list({
        calendarId: 'primary',
        timeMin: start.toISOString(),
        timeMax: end.toISOString(),
        showDeleted: false,
        singleEvents: true,
        orderBy: 'startTime',
        });

        console.log('События недели:', res.result.items);
    }
    

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
                {getWeekDays().map((day, index) => (
                    <button 
                    key={index} 
                    className={`day-btn ${isToday(day) ? 'today' : ''}`}
                    >
                    <div>{format(day, 'EEEE, d')}</div>
                    </button>
                ))}
            </div>
        </div>
        <div className="recs-section">
            <div className="recs-header">
                <h1 className="recs-title">Recommendations on tasks</h1>
            </div>
            <div className="recs-content">

            </div>
        </div>
    </div>
    );
}

export default AiSchedule;