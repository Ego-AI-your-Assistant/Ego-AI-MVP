import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    navigate("/reg-page", { replace: true });
  };

  useEffect(() => {
    const nav = document.querySelector('.nav');
    const height = nav?.getBoundingClientRect().height || 0;
    document.documentElement.style.setProperty('--nav-height', `${height}px`);
  }, []);
  
  return (
    <div className="layout">
      <nav className="nav">
        <div className="nav-links">
          <Link to="/calendar" className="nav-link">Calendar</Link> {/* Fill with links to pages */}
          <Link to="/chat" className="nav-link">Chat with AI</Link>
          <Link to="" className="nav-link">Dashboard/Analytics</Link> 
          <Link to="/recs" className="nav-link">Recommendations</Link>
          <Link to="/geo-search" className='nav-link'>GEO-ASSISTANT</Link>
          <Link to="/profile" className="nav-link">Profile</Link>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout; 