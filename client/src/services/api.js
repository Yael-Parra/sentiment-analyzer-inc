/ src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  async analyzeVideo(videoData) {
    try {
      const response = await fetch(`${API_BASE_URL}/predict/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(videoData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing video:', error);
      throw error;
    }
  }

  async getStats(videoId, maxComments = 100) {
    try {
      const response = await fetch(`${API_BASE_URL}/stats/?video_id=${videoId}&max_comments=${maxComments}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  }

  async getSavedComments(videoId) {
    try {
      const response = await fetch(`${API_BASE_URL}/saved-comments/${videoId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching saved comments:', error);
      throw error;
    }
  }

  async deleteSavedComments(videoId) {
    try {
      const response = await fetch(`${API_BASE_URL}/saved-comments/${videoId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting saved comments:', error);
      throw error;
    }
  }

  async extractComments(videoData) {
    try {
      const response = await fetch(`${API_BASE_URL}/extract-comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(videoData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error extracting comments:', error);
      throw error;
    }
  }
}

export default new ApiService();