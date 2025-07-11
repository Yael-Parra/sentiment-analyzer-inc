import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Función para normalizar comentarios (mapear campos del backend al frontend)
const normalizeComment = (comment) => ({
  ...comment,
  // Mapear like_count_comment a like_count si existe
  like_count: comment.like_count ?? comment.like_count_comment ?? 0,
});

// Función para normalizar array de comentarios
const normalizeComments = (comments) => {
  if (!Array.isArray(comments)) return [];
  return comments.map(normalizeComment);
};

// Analyze YouTube video
export const analyzeYouTubeVideo = async (videoUrl, maxComments = 100) => {
    try {
        const response = await axios.post(`${API_URL}/CommentAnalyzer/`, {
            url_or_id: videoUrl,
            max_comments: maxComments
        });
        
        // Normalizar los comentarios en la respuesta
        if (response.data.comments) {
            response.data.comments = normalizeComments(response.data.comments);
        }
        
        return response.data;
    } catch (error) {
        console.error('❌ Error analyzing video:', error.message);
        throw new Error(`Error while analyzing video: ${error.response?.data?.detail || error.message}`);
    }
};

// Get video statistics
export async function getVideoStatistics(videoId) {
  try {
    const res = await fetch(`http://localhost:5000/statistics/${videoId}`);
    if (!res.ok) throw new Error("Error en la petición de estadísticas");
    const data = await res.json();
    
    // Normalizar comentarios si existen en las estadísticas
    if (data.comments) {
      data.comments = normalizeComments(data.comments);
    }
    
    return data;
  } catch (err) {
    console.error("getVideoStatistics error:", err);
    return null;
  }
};

// Función para obtener comentarios del video
export const getCommentsByVideo = async (videoId) => {
  try {
    const response = await fetch(`/api/videos/${videoId}/comments`);
    if (!response.ok) throw new Error('Error al obtener comentarios');
    const data = await response.json();
    const comments = Array.isArray(data) ? data : [];
    return normalizeComments(comments);
  } catch (error) {
    console.error('Error en getCommentsByVideo:', error);
    throw error;
  }
};

// Get saved comments
export const getSavedComments = async (videoId) => {
    try {
        const response = await axios.get(`${API_URL}/saved-comments/${videoId}`);
        
        // Normalizar comentarios si existen
        if (response.data.comments) {
            response.data.comments = normalizeComments(response.data.comments);
        }
        
        return response.data;
    } catch (error) {
        console.error('❌ Error getting saved comments:', error.message);
        throw new Error(`Error while obtaining saved comments: ${error.response?.data?.detail || error.message}`);
    }
};

// Delete saved comments
export const deleteSavedComments = async (videoId) => {
    try {
        const response = await axios.delete(`${API_URL}/saved-comments/${videoId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error deleting saved comments:', error.message);
        throw new Error(`Error while eliminating comments: ${error.response?.data?.detail || error.message}`);
    }
};

// Server health check
export const checkServerHealth = async () => {
    try {
        const response = await axios.get(`${API_URL}/`);
        return response.data;
    } catch (error) {
        console.error('❌ Server health check failed:', error.message);
        throw new Error(`Servidor not avilable: ${error.message}`);
    }
};

// Toxicity chart data
export const formatToxicityDataForCharts = (toxicityStats = {}) => {
  return [
    {
      name: 'Toxicidad',
      toxic: toxicityStats.toxic_count || 0,
      nonToxic: toxicityStats.non_toxic_count || 0
    }
  ];
};

// Función para calcular métricas de engagement (con normalización)
export const calculateEngagementMetrics = (comments = []) => {
  if (!comments.length) return {};
  
  const normalizedComments = normalizeComments(comments);
  const totalLikes = normalizedComments.reduce((sum, c) => sum + (c.like_count || 0), 0);
  const maxLikes = Math.max(...normalizedComments.map(c => c.like_count || 0));
  
  return {
    mean_likes: totalLikes / normalizedComments.length,
    max_likes: maxLikes,
    total_likes: totalLikes
  };
};

const TOXICITY_COLORS = {
    'is_toxic': '#FF6B6B',
    'is_hatespeech': '#FF4757',
    'is_abusive': '#FF3838',
    'is_provocative': '#FF6348',
    'is_racist': '#FF5252',
    'is_obscene': '#FF7675',
    'is_threat': '#D63031',
    'is_religious_hate': '#E17055',
    'is_nationalist': '#A29BFE',
    'is_sexist': '#FD79A8',
    'is_homophobic': '#FDCB6E',
    'is_radicalism': '#6C5CE7'
};

const getToxicityColor = (type) => TOXICITY_COLORS[type] || '#74B9FF';

// Sentiment chart data
export const formatSentimentDataForCharts = (sentimentAnalysis) => {
    if (!sentimentAnalysis?.sentiment_counts) return [];
    
    const total = Object.values(sentimentAnalysis.sentiment_counts).reduce((a, b) => a + b, 0);
    
    return Object.entries(sentimentAnalysis.sentiment_counts).map(([sentiment, count]) => ({
        sentiment: sentiment.toUpperCase(),
        count,
        percentage: total > 0 ? ((count / total) * 100).toFixed(1) : 0,
        color: getSentimentColor(sentiment)
    }));
};

const SENTIMENT_COLORS = {
    'positive': '#00B894',
    'negative': '#E17055',
    'neutral' : '#74B9FF',
};

const getSentimentColor = (sentiment) => SENTIMENT_COLORS[sentiment.toLowerCase()] || '#DDD';

// Filter comments (con normalización)
export const filterComments = (comments, filters) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    return normalizedComments.filter(comment => {
        if (typeof filters.minToxicity === 'number' && comment.toxic_probability < filters.minToxicity) {
            return false;
        }
        if (filters.toxicityType && !comment[`is_${filters.toxicityType}`]) {
            return false;
        }
        if (filters.searchText && !comment.text.toLowerCase().includes(filters.searchText.toLowerCase())) {
            return false;
        }
        if (typeof filters.minLikes === 'number' && comment.like_count < filters.minLikes) {
            return false;
        }
        return true;
    });
};

// Top toxic comments (con normalización)
export const getTopToxicComments = (comments, limit = 5) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    return normalizedComments
        .filter(comment => comment.toxic_probability > 0)
        .sort((a, b) => b.toxic_probability - a.toxic_probability)
        .slice(0, limit);
};

// Extract video ID
export const extractVideoIdFromUrl = (url) => {
  const pattern = /(?:v=|\/)([0-9A-Za-z_-]{11})/;
  const match = url.match(pattern);
  if (match && match[1]) {
    return match[1];
  }
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

// Detect sarcastic toxic comments (con normalización)
export const formatSarcasmDataForDisplay = (comments) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    return normalizedComments.filter(comment =>
        comment.is_toxic && comment.sentiment_type === 'positive'
    );
};

// Top liked comments (con normalización)
export const getTopLikedComments = (comments, limit = 5) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    return normalizedComments
        .filter(comment => typeof comment.like_count === 'number')
        .sort((a, b) => b.like_count - a.like_count)
        .slice(0, limit);
};

// Sentiment intensity distribution (con normalización)
export const getSentimentIntensityDistribution = (comments) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    const bins = {
        '0.0 - 0.3': 0,
        '0.3 - 0.6': 0,
        '0.6 - 1.0': 0
    };

    normalizedComments.forEach(comment => {
        const intensity = comment.sentiment_score || 0;
        if (intensity <= 0.3) bins['0.0 - 0.3'] += 1;
        else if (intensity <= 0.6) bins['0.3 - 0.6'] += 1;
        else bins['0.6 - 1.0'] += 1;
    });

    return Object.entries(bins).map(([range, count]) => ({ range, count }));
};

// Toxicity vs. likes scatter plot data (con normalización)
export const getToxicityEngagementScatterData = (comments) => {
    if (!comments || !Array.isArray(comments)) return [];

    const normalizedComments = normalizeComments(comments);
    
    return normalizedComments
        .filter(c => typeof c.toxic_probability === 'number')
        .map(c => ({
            likeCount: c.like_count || 0,
            toxicity: c.toxic_probability,
            sentiment: c.sentiment_type
        }));
};

export const getStrategicInsights = (stats) => ({
    sarcasmWarning: stats.sarcasm_ratio > 0.2 ? "⚠️ High sarcasm" : "✅",
    bestTimeToPost: stats.optimal_posting_time,
    topTrolls: stats.top_toxic_authors
});