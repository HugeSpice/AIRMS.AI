

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('authToken');
          window.location.href = '/';
          throw new Error('Unauthorized');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    return this.request<{
      access_token: string;
      token_type: string;
      expires_in: number;
      user: any;
    }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email: string, password: string, fullName: string) {
    return this.request<any>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async getCurrentUser() {
    return this.request<any>('/api/v1/auth/me');
  }

  // API Key management
  async generateApiKey(name: string) {
    return this.request<any>('/api/v1/api-keys', {
      method: 'POST',
      body: JSON.stringify({ key_name: name }),
    });
  }

  async revokeApiKey(keyId: string) {
    return this.request<any>(`/api/v1/api-keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  async getApiKeys() {
    return this.request<any[]>('/api/v1/api-keys');
  }

  // Risk detection endpoints
  async detectRisks(content: string) {
    return this.request<any>('/api/v1/risk/detect', {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  async getRiskHistory() {
    return this.request<any[]>('/api/v1/risk/history');
  }

  async getRiskAnalytics() {
    return this.request<any>('/api/v1/risk/analytics');
  }

  // System endpoints
  async getSystemStatus() {
    return this.request<any>('/api/v1/system/status');
  }

  async getSystemSettings() {
    return this.request<any>('/api/v1/system/settings');
  }

  async updateSystemSettings(settings: any) {
    return this.request<any>('/api/v1/system/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }
}

export const apiService = new ApiService();
export default apiService;
