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
  private baseUrl = '/api/v1/recommend';

  async getRecommendations(): Promise<RecommendedPlace[]> {
    try {
      console.log('[FRONTEND] Making request to recommendations API...');
      const response = await fetch(`${this.baseUrl}`, {
        method: 'POST',
        credentials: 'include',
      });
      
      console.log(`[FRONTEND] Response status: ${response.status}`);
      console.log(`[FRONTEND] Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[FRONTEND] HTTP error! status: ${response.status}, body: ${errorText}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const rawText = await response.text();
      console.log(`[FRONTEND] Raw response text: ${rawText}`);
      
      let result;
      try {
        result = JSON.parse(rawText);
        console.log(`[FRONTEND] Parsed JSON result:`, result);
      } catch (jsonError) {
        console.error(`[FRONTEND] Failed to parse response as JSON: ${jsonError}`);
        console.error(`[FRONTEND] Raw text that failed to parse: ${rawText}`);
        throw new Error(`Failed to parse response as JSON: ${rawText}`);
      }
      
      const recommendations = result.recommendations || [];
      console.log(`[FRONTEND] Extracted recommendations:`, recommendations);
      
      // Validate recommendations structure
      const validRecommendations = recommendations.filter((rec: any, index: number) => {
        const isValid = rec && 
               typeof rec.id === 'string' && 
               typeof rec.title === 'string' && 
               typeof rec.description === 'string' &&
               typeof rec.address === 'string' &&
               typeof rec.lat === 'number' && 
               typeof rec.lon === 'number' &&
               typeof rec.category === 'string';
        
        if (!isValid) {
          console.warn(`[FRONTEND] Invalid recommendation at index ${index}:`, rec);
          console.warn(`[FRONTEND] Field types:`, {
            id: typeof rec?.id,
            title: typeof rec?.title,
            description: typeof rec?.description,
            address: typeof rec?.address,
            lat: typeof rec?.lat,
            lon: typeof rec?.lon,
            category: typeof rec?.category
          });
        }
        
        return isValid;
      });
      
      console.log(`[FRONTEND] Valid recommendations count: ${validRecommendations.length}`);
      return validRecommendations;
    } catch (error) {
      console.error('[FRONTEND] Error fetching recommendations:', error);
      console.log('[FRONTEND] Falling back to mock recommendations');
      return this.getMockRecommendations();
    }
  }

  /*
  async addRecommendation(place: CreateRecommendationRequest): Promise<RecommendedPlace | null> {
    try {
      const response = await fetch(`${this.baseUrl}/places`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(place),
        credentials: 'include',
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
        credentials: 'include',
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
*/

  async updateRecommendation(id: string, updates: Partial<CreateRecommendationRequest>): Promise<RecommendedPlace | null> {
    try {
      const response = await fetch(`${this.baseUrl}/places/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
        credentials: 'include',
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
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