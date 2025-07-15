import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './GeoSearch.css';
import { recommendationsApi, type RecommendedPlace } from '../../utils/recommendationsApi';

// Fix Leaflet icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface SearchResult {
  id: string;
  title: string;
  description: string;
  address: string;
  lat: number;
  lon: number;
  type?: string;
  importance?: number;
}

// RecommendedPlace interface imported from recommendationsApi

interface MapUpdaterProps {
  center: [number, number];
  zoom: number;
}

// Component for updating map center
const MapUpdater: React.FC<MapUpdaterProps> = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);
  
  return null;
};

export const GeoSearch: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [recommendedPlaces, setRecommendedPlaces] = useState<RecommendedPlace[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>([55.7558, 37.6173]); // Moscow
  const [mapZoom, setMapZoom] = useState(10);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<RecommendedPlace | null>(null);

  // Creating custom marker icons
  const searchIcon = L.divIcon({
    html: `
      <div style="
        width: 20px;
        height: 20px;
        background: linear-gradient(135deg, #10a37f 0%, #059669 100%);
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      "></div>
    `,
    className: 'custom-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -10]
  });

  const recommendedIcon = L.divIcon({
    html: `
      <div style="
        width: 20px;
        height: 20px;
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      "></div>
    `,
    className: 'custom-marker recommended',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -10]
  });

  // Search places via Nominatim API (OpenStreetMap)
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setSelectedResult(null);

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=10&addressdetails=1&extratags=1`
      );
      
             if (!response.ok) {
         throw new Error('Search error');
       }

      const data = await response.json();
      
      const results: SearchResult[] = data.map((item: any, index: number) => ({
        id: item.place_id || index.toString(),
                 title: item.display_name.split(',')[0] || item.name || 'Place',
         description: item.type || item.class || 'Place',
        address: item.display_name,
        lat: parseFloat(item.lat),
        lon: parseFloat(item.lon),
        type: item.type,
        importance: item.importance
      }));

      setSearchResults(results);

             // Center map on first result
      if (results.length > 0) {
        const firstResult = results[0];
        setMapCenter([firstResult.lat, firstResult.lon]);
        setMapZoom(13);
      }

         } catch (error) {
       console.error('Search error:', error);
       // Can add error notification
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setSelectedResult(result);
    setSelectedRecommendation(null);
    setMapCenter([result.lat, result.lon]);
    setMapZoom(15);
  };

  const handleRecommendationClick = (place: RecommendedPlace) => {
    setSelectedRecommendation(place);
    setSelectedResult(null);
    setMapCenter([place.lat, place.lon]);
    setMapZoom(15);
  };

  const getDistance = (lat: number, lon: number) => {
    // Simple distance calculation from Moscow center
    const moscowLat = 55.7558;
    const moscowLon = 37.6173;
    
    const R = 6371; // Earth radius in km
    const dLat = (lat - moscowLat) * Math.PI / 180;
    const dLon = (lon - moscowLon) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(moscowLat * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    
    if (distance < 1) {
      return `${Math.round(distance * 1000)} m`;
    } else {
      return `${distance.toFixed(1)} km`;
    }
  };

  // API functions for recommendations
  const fetchRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      const data = await recommendationsApi.getRecommendations();
      setRecommendedPlaces(data);
    } catch (error) {
      console.error('Error loading recommendations:', error);
      setRecommendedPlaces([]);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  /*
  const removeRecommendation = async (id: string) => {
    try {
      const success = await recommendationsApi.removeRecommendation(id);
      if (success) {
        setRecommendedPlaces(prev => prev.filter(place => place.id !== id));
        if (selectedRecommendation?.id === id) {
          setSelectedRecommendation(null);
        }
        return true;
      }
    } catch (error) {
      console.error('Error removing recommendation:', error);
    }
    return false;
  };
*/

  // Load recommendations on component mount
  useEffect(() => {
    fetchRecommendations();
  }, []);

  return (
    <div className="geo-search-container">
      <div className="geo-search-content">
        {/* Left panel with recommendations */}
        <div className="recommendations-sidebar">
          <div className="recommendations-header">
            <h2>Recommendations</h2>
            <button 
              onClick={fetchRecommendations}
              disabled={isLoadingRecommendations}
              className="refresh-btn"
              title="Refresh recommendations"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path
                  d="M1 4V10H7M23 20V14H17M20.49 9A9 9 0 0 0 5.64 5.64L1 10M23 14L18.36 18.36A9 9 0 0 1 3.51 15"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>

          <div className="recommendations-container">
            {isLoadingRecommendations ? (
              <div className="loading-recommendations">
                <div className="loading-spinner"></div>
                <p>Loading recommendations...</p>
              </div>
            ) : recommendedPlaces.length === 0 ? (
              <div className="no-recommendations">
                <div className="no-recommendations-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <p>No recommendations</p>
              </div>
            ) : (
              <div className="recommendations-list">
                {recommendedPlaces.map((place) => (
                  <div 
                    key={place.id} 
                    className={`recommendation-item ${selectedRecommendation?.id === place.id ? 'selected' : ''}`}
                    onClick={() => handleRecommendationClick(place)}
                  >
                    <div className="recommendation-header">
                      <h3 className="recommendation-title">{place.title}</h3>
                      <div className="recommendation-actions">
                        {place.rating && (
                          <div className="recommendation-rating">
                            <span className="rating-stars">⭐</span>
                            <span>{place.rating}</span>
                          </div>
                        )}
                        {/*
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeRecommendation(place.id);
                          }}
                          className="remove-btn"
                          title="Remove recommendation"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                            <path
                              d="M18 6L6 18M6 6L18 18"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </button>
                        */}
                      </div>
                    </div>
                    <p className="recommendation-category">{place.category}</p>
                    <p className="recommendation-description">{place.description}</p>
                    <p className="recommendation-address">{place.address}</p>
                    <p className="recommendation-distance">
                      📍 {getDistance(place.lat, place.lon)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        {/* Map section */}
        <div className="map-section">
          <div className="search-controls">
            <div className="search-input-container">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search places, addresses, establishments..."
                className="search-input"
                disabled={isLoading}
              />
              <button
                onClick={handleSearch}
                disabled={isLoading || !searchQuery.trim()}
                className="search-button"
              >
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M21 21L16.514 16.506M19 10.5C19 15.194 15.194 19 10.5 19S2 15.194 2 10.5 5.806 2 10.5 2 19 5.806 19 10.5Z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
          
          <div className="map-container">
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '100%', width: '100%' }}
              zoomControl={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              <MapUpdater center={mapCenter} zoom={mapZoom} />
              
                             {searchResults.map((result) => (
                 <Marker
                   key={`search-${result.id}`}
                   position={[result.lat, result.lon]}
                   icon={searchIcon}
                   eventHandlers={{
                     click: () => setSelectedResult(result)
                   }}
                 >
                   <Popup>
                     <div style={{ padding: '8px', minWidth: '200px' }}>
                       <h3 style={{ 
                         margin: '0 0 4px 0', 
                         color: '#10a37f',
                         fontSize: '16px',
                         fontWeight: '600'
                       }}>
                         {result.title}
                       </h3>
                       <p style={{ 
                         margin: '0 0 4px 0', 
                         color: '#666', 
                         fontSize: '14px' 
                       }}>
                         {result.address}
                       </p>
                       <p style={{ 
                         margin: '4px 0 0 0', 
                         color: '#666', 
                         fontSize: '12px' 
                       }}>
                         Type: {result.type || result.description}
                       </p>
                     </div>
                   </Popup>
                 </Marker>
               ))}
               
               {recommendedPlaces.map((place) => (
                 <Marker
                   key={`recommended-${place.id}`}
                   position={[place.lat, place.lon]}
                   icon={recommendedIcon}
                   eventHandlers={{
                     click: () => setSelectedRecommendation(place)
                   }}
                 >
                   <Popup>
                     <div style={{ padding: '8px', minWidth: '200px' }}>
                       <h3 style={{ 
                         margin: '0 0 4px 0', 
                         color: '#7c3aed',
                         fontSize: '16px',
                         fontWeight: '600'
                       }}>
                         {place.title}
                       </h3>
                       <p style={{ 
                         margin: '0 0 4px 0', 
                         color: '#666', 
                         fontSize: '14px' 
                       }}>
                         {place.address}
                       </p>
                       <p style={{ 
                         margin: '4px 0 4px 0', 
                         color: '#666', 
                         fontSize: '12px' 
                       }}>
                         {place.category}
                       </p>
                       {place.rating && (
                         <p style={{ 
                           margin: '4px 0 0 0', 
                           color: '#666', 
                           fontSize: '12px' 
                         }}>
                           Rating: {place.rating}/5
                         </p>
                       )}
                     </div>
                   </Popup>
                 </Marker>
               ))}
            </MapContainer>
          </div>
        </div>

        {/* Right sidebar with results */}
        <div className="results-sidebar">
          <div className="results-header">
            <h2>Search Results</h2>
            {searchResults.length > 0 && (
              <span className="results-count">
                Found: {searchResults.length}
              </span>
            )}
          </div>

          <div className="results-container">
            {searchResults.length === 0 ? (
              <div className="no-results">
                <div className="no-results-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M21 21L16.514 16.506M19 10.5C19 15.194 15.194 19 10.5 19S2 15.194 2 10.5 5.806 2 10.5 2 19 5.806 19 10.5Z"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <p>Enter a query to search for places</p>
              </div>
            ) : (
              <div className="results-list">
                {searchResults.map((result) => (
                  <div 
                    key={result.id} 
                    className={`result-item ${selectedResult?.id === result.id ? 'selected' : ''}`}
                    onClick={() => handleResultClick(result)}
                  >
                    <div className="result-header">
                      <h3 className="result-title">{result.title}</h3>
                      {result.importance && (
                        <div className="result-rating">
                          <span className="rating-stars">⭐</span>
                          <span>{Math.round(result.importance * 10)}/10</span>
                        </div>
                      )}
                    </div>
                    <p className="result-description">
                      {result.type || result.description}
                    </p>
                    <p className="result-address">{result.address}</p>
                                         <p className="result-distance">
                       📍 {getDistance(result.lat, result.lon)}
                     </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeoSearch; 