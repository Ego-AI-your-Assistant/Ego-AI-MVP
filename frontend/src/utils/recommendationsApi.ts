export interface RecommendedPlace {
  id: string;
  title: string;
  description: string;
  address: string;
  lat: number;
  lon: number;
  category: string;
  rating?: number;
  image?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface CreateRecommendationRequest {
  title: string;
  description: string;
  address: string;
  lat: number;
  lon: number;
  category: string;
  rating?: number;
  image?: string;
}

export interface RecommendationsResponse {
  success: boolean;
  data: RecommendedPlace[];
  total: number;
}

export interface RecommendationResponse {
  success: boolean;
  data: RecommendedPlace;
}

export interface ApiError {
  success: false;
  error: string;
  code?: number;
}

class RecommendationsApi {
  private baseUrl = '/api/v1/recommendations';

  async getRecommendations(): Promise<RecommendedPlace[]> {
    try {
      const response = await fetch('/recommend', {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      return result.recommendations || [];
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      return this.getMockRecommendations();
    }
  }

  async addRecommendation(place: CreateRecommendationRequest): Promise<RecommendedPlace | null> {
    try {
      const response = await fetch(`${this.baseUrl}/places`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(place),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: RecommendationResponse = await response.json();
      return result.data;
    } catch (error) {
      console.error('Error adding recommendation:', error);
      return null;
    }
  }

  async removeRecommendation(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/places/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error removing recommendation:', error);
      return false;
    }
  }

  async updateRecommendation(id: string, updates: Partial<CreateRecommendationRequest>): Promise<RecommendedPlace | null> {
    try {
      const response = await fetch(`${this.baseUrl}/places/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: RecommendationResponse = await response.json();
      return result.data;
    } catch (error) {
      console.error('Error updating recommendation:', error);
      return null;
    }
  }

  private getMockRecommendations(): RecommendedPlace[] {
          return [
        {
          id: '1',
          title: 'Red Square',
          description: 'Main square of Russia, symbol of the country',
          address: 'Red Square, Moscow, 109012',
          lat: 55.7539,
          lon: 37.6208,
          category: 'Attraction',
          rating: 4.8,
          createdAt: new Date().toISOString()
        },
        {
          id: '2',
          title: 'Gorky Park',
          description: 'Central park of culture and recreation',
          address: 'Krymsky Val St, 9, Moscow, 119049',
          lat: 55.7312,
          lon: 37.6014,
          category: 'Park',
          rating: 4.5,
          createdAt: new Date().toISOString()
        },
        {
          id: '3',
          title: 'Tretyakov Gallery',
          description: 'State gallery of Russian art',
          address: 'Lavrushinsky Lane, 10, Moscow, 119017',
          lat: 55.7414,
          lon: 37.6207,
          category: 'Museum',
          rating: 4.7,
          createdAt: new Date().toISOString()
        },
        {
          id: '4',
          title: 'VDNKh',
          description: 'Exhibition of achievements of national economy',
          address: 'Mira Ave, 119, Moscow, 129223',
          lat: 55.8304,
          lon: 37.6327,
          category: 'Exhibition Center',
          rating: 4.6,
          createdAt: new Date().toISOString()
        },
        {
          id: '5',
          title: 'Moscow Kremlin',
          description: 'Historic fortress in the center of Moscow',
          address: 'Moscow, 103132',
          lat: 55.7520,
          lon: 37.6175,
          category: 'Attraction',
          rating: 4.9,
          createdAt: new Date().toISOString()
        }
      ];
  }

  // Utility methods
  static calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): string {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    
    if (distance < 1) {
      return `${Math.round(distance * 1000)} m`;
    } else {
      return `${distance.toFixed(1)} km`;
    }
  }

  static validateCoordinates(lat: number, lon: number): boolean {
    return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
  }

  static formatCategory(category: string): string {
    const categories: Record<string, string> = {
      'restaurant': 'Restaurant',
      'cafe': 'Cafe',
      'museum': 'Museum',
      'park': 'Park',
      'attraction': 'Attraction',
      'shopping': 'Shopping',
      'hotel': 'Hotel',
      'hospital': 'Hospital',
      'school': 'School',
      'university': 'University',
      'bank': 'Bank',
      'gas_station': 'Gas Station',
      'pharmacy': 'Pharmacy'
    };
    
    return categories[category] || category;
  }
}

export const recommendationsApi = new RecommendationsApi();
export default recommendationsApi; 