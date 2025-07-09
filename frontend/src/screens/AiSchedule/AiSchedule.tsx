import React, { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isToday } from 'date-fns';
import { fetchEvents } from '@/utils/calendarApi';
import './AiSchedule.css';

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
        </div>
        <div className="recommendations-section"></div>
    </div>
    );
}

export default AiSchedule;