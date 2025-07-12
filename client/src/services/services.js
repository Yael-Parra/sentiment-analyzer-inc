import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Analyze YouTube video
export const analyzeYouTubeVideo = async (videoUrl, maxComments = 100) => {
    try {
        const response = await axios.post(`${API_URL}/CommentAnalyzer/`, {
            url_or_id: videoUrl,
            max_comments: maxComments
        });
        return response.data
    } catch (error) {
        console.error('❌ Error analyzing video:', error.message);
        throw new Error(`Error while analyzing video: ${error.response?.data?.detail || error.message}`);
    }
};

// Sentiment Analyzer Services //

// Get all sentime analyzer data
export const getSentimentAnalyzerAll = async () => {
    try {
        const response = await axios.get(`${API_URL}/sentiment-analyzer/all`);
        return response.data;
    } catch (error) {
        console.error('❌ Error getting all sentiment analyzer data:', error.message);
        throw new Error(`Error while obtaining all sentiment data: ${error.response?.data?.detail || error.message}`);
    }
};

// Get sentiment analyzer data by video ID
export const getSentimentAnalyzerByVideo = async (videoId) => {
    if (!videoId) {
        throw new Error("Se requiere el ID del video para obtener datos de sentiment analyzer");
    }
    
    try {
        // Convertir videoId (camelCase) a video_id (snake_case) para el endpoint
        const response = await axios.get(`${API_URL}/sentiment-analyzer/video/${videoId}`);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data?.detail || 
                          (error.response?.status === 404 ? 
                           `No se encontraron comentarios para el video ${videoId}` : 
                           error.message);
        console.error('❌ Error getting sentiment analyzer data by video:', errorMessage);
        throw new Error(`Error while obtaining sentiment data: ${errorMessage}`);
    }
};

// Video Statistics Services //
// Get all video statistics
export const getVideoStatisticsAll = async () => {
    try {
        const response = await axios.get(`${API_URL}/video-statistics/all`);
        return response.data;
    } catch (error) {
        console.error('❌ Error getting all video statistics:', error.message);
        throw new Error(`Error while obtaining all video statistics: ${error.response?.data?.detail || error.message}`);
    }
};

// Get video statistics by video ID
export const getVideoStatisticsById = async (videoId) => {
    if (!videoId) {
        throw new Error("Se requiere el ID del video para obtener estadísticas");
    }
    
    try {
        const response = await axios.get(`${API_URL}/video-statistics/video/${videoId}`);
        return response.data;
    } catch (error) {
        const errorMessage = error.response?.data?.detail || 
                          (error.response?.status === 404 ? 
                           `No se encontraron estadísticas para el video ${videoId}` : 
                           error.message);
        console.error('❌ Error getting video statistics by ID:', errorMessage);
        throw new Error(`Error while obtaining video statistics: ${errorMessage}`);
    }
};

// Saved Comments Services //

// Get Saved Comments 
export const getSavedComments = async (videoId) => {
    try {
        const response = await axios.get(`${API_URL}/saved-comments/${videoId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error getting saved comments:', error.message);
        throw new Error(`Error while obtaining saved comments: ${error.response?.data?.detail || error.message}`);
    }
};

// Delete Saved Comments //
export const deleteSavedComments = async (videoId) => {
    try {
        const response = await axios.delete(`${API_URL}/saved-comments/${videoId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error deleting saved comments:', error.message);
        throw new Error(`Error while eliminating comments: ${error.response?.data?.detail || error.message}`);
    }
};


// Server Health Services //


// Server Health Check
export const checkServerHealth = async () => {
    try {
        const response = await axios.get(`${API_URL}/`);
        return response.data;
    } catch (error) {
        console.error('❌ Server health check failed:', error.message);
        throw new Error(`Servidor not avilable: ${error.message}`);
    }
};


// Utility Functions //

// Extract Video ID
export const extractVideoIdFromUrl = (url) => {
  // Match "v=" o "/" seguido de 11 caracteres válidos para un ID de YouTube
  const pattern = /(?:v=|\/)([0-9A-Za-z_-]{11})/;
  const match = url.match(pattern);
  if (match && match[1]) {
    return match[1];
  }
  // Si no se encuentra nada, asume que la entrada es un ID directo
  return url; 
};

// Validate YouTube URL or ID
export const isValidYouTubeUrl = (url) => {
    const patterns = [
        /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[a-zA-Z0-9_-]{11}/,
        /^[a-zA-Z0-9_-]{11}$/
    ];
    return patterns.some(pattern => pattern.test(url));
};