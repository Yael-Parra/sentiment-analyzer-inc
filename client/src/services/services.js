import axios from "axios";

export const API_URL = 'http://127.0.0.1:8000';

export const analyzeYouTubeVideo = async (videoUrl, maxComments = 100) => {
    try {
        const response = await axios.post(`${API_URL}/predict/`, {
            url_or_id: videoUrl,
            max_comments: maxComments
        });
        return response.data;
    } catch (error) {
        console.error('❌ Error analyzing video:', error.message);
        throw new Error(`Error al analizar el video: ${error.response?.data?.detail || error.message}`);
    }
};

/**Servicio para estadísticas **/
export const getVideoStatistics = async (videoId, maxComments = 100) => {
    try {
        const response = await axios.get(`${API_URL}/stats/`, {
            params: {
                video_id: videoId,
                max_comments: maxComments
            }
        });
        return response.data;
    } catch (error) {
        console.error('❌ Error getting stats:', error.message);
        throw new Error(`Error al obtener estadísticas: ${error.response?.data?.detail || error.message}`);
    }
};

/**Obtener comentarios guardados
 * Endpoint: GET /saved-comments/{video_id}
 */
export const getSavedComments = async (videoId) => {
    try {
        const response = await axios.get(`${API_URL}/saved-comments/${videoId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error getting saved comments:', error.message);
        throw new Error(`Error al obtener comentarios guardados: ${error.response?.data?.detail || error.message}`);
    }
};

/** Eliminar comentarios guardados por id, endpoint: DELETE /saved-comments/{video_id}*/
export const deleteSavedComments = async (videoId) => {
    try {
        const confirmed = window.confirm(
            `¿Estás seguro de eliminar todos los comentarios guardados del video ${videoId}?`
        );
        
        if (!confirmed) return null;
        
        const response = await axios.delete(`${API_URL}/saved-comments/${videoId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error deleting saved comments:', error.message);
        throw new Error(`Error al eliminar comentarios: ${error.response?.data?.detail || error.message}`);
    }
};

/**  Health check del servidor
 * Endpoint: GET /
 */
export const checkServerHealth = async () => {
    try {
        const response = await axios.get(`${API_URL}/`);
        return response.data;
    } catch (error) {
        console.error('❌ Server health check failed:', error.message);
        throw new Error(`Servidor no disponible: ${error.message}`);
    }
};
 
/**  FUNCIONES OPCIONALES PARA COSAS DEL FRONT
 *  Formatear datos de toxicidad para gráficos
 */
export const formatToxicityDataForCharts = (barras_toxicidad) => {
    if (!barras_toxicidad) return [];
    
    return Object.entries(barras_toxicidad).map(([type, data]) => {
        const total = data.true + data.false;
        return {
            type: type.replace('is_', '').toUpperCase(),
            positive: data.true,
            negative: data.false,
            total: total,
            percentage: total > 0 ? ((data.true / total) * 100).toFixed(1) : 0,
            color: getToxicityColor(type)
        };
    });
};

/**
 *  Obtener color para tipo de toxicidad
 */
const getToxicityColor = (type) => {
    const colors = {
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
    return colors[type] || '#74B9FF';
};

/**
 *  Formatear datos de sentimiento para gráficos
 */
export const formatSentimentDataForCharts = (sentimientos) => {
    if (!sentimientos?.sentiment_types_distribution) return [];
    
    return Object.entries(sentimientos.sentiment_types_distribution).map(([sentiment, count]) => ({
        sentiment: sentiment.toUpperCase(),
        count: count,
        percentage: count > 0 ? ((count / Object.values(sentimientos.sentiment_types_distribution).reduce((a, b) => a + b, 0)) * 100).toFixed(1) : 0,
        color: getSentimentColor(sentiment)
    }));
};

/**
 *  Obtener color para tipo de sentimiento
 */
const getSentimentColor = (sentiment) => {
    const colors = {
        'positive': '#00B894',
        'negative': '#E17055',
        'neutral': '#74B9FF',
        'compound': '#FDCB6E'
    };
    return colors[sentiment.toLowerCase()] || '#DDD';
};

/**
 *  Filtrar comentarios por criterios
 */
export const filterComments = (comments, filters) => {
    if (!comments || !Array.isArray(comments)) return [];
    
    return comments.filter(comment => {
        // Filtro por toxicidad
        if (filters.minToxicity && comment.toxic_probability < filters.minToxicity) {
            return false;
        }
        
        // Filtro por tipo específico
        if (filters.toxicityType && !comment[`is_${filters.toxicityType}`]) {
            return false;
        }
        
        // Filtro por texto
        if (filters.searchText && !comment.text.toLowerCase().includes(filters.searchText.toLowerCase())) {
            return false;
        }
        
        // Filtro por likes mínimos
        if (filters.minLikes && comment.like_count < filters.minLikes) {
            return false;
        }
        
        return true;
    });
};

/**
 *  Obtener top comentarios más tóxicos
 */
export const getTopToxicComments = (comments, limit = 5) => {
    if (!comments || !Array.isArray(comments)) return [];
    
    return comments
        .filter(comment => comment.toxic_probability > 0)
        .sort((a, b) => b.toxic_probability - a.toxic_probability)
        .slice(0, limit);
};

/**
 * Calcular métricas de engagement
 */
export const calculateEngagementMetrics = (comments, engagement_stats) => {
    if (!comments || !Array.isArray(comments)) return null;
    
    const totalComments = comments.length;
    const totalLikes = comments.reduce((sum, comment) => sum + (comment.like_count || 0), 0);
    
    return {
        totalComments,
        averageLikes: totalComments > 0 ? (totalLikes / totalComments).toFixed(2) : 0,
        maxLikes: Math.max(...comments.map(c => c.like_count || 0)),
        commentsWithUrls: engagement_stats?.comments_with_urls || 0,
        commentsWithTags: engagement_stats?.comments_with_tags || 0,
        urlPercentage: engagement_stats?.url_percentage || 0,
        tagPercentage: engagement_stats?.tag_percentage || 0
    };
};

/**
 *  Extraer ID de video de URL de YouTube
 */
export const extractVideoIdFromUrl = (url) => {
    const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)/;
    const match = url.match(regex);
    return match ? match[1] : url; // Si no encuentra patrón, asume que ya es ID
};

/**
 *  Validar URL de YouTube
 */
export const isValidYouTubeUrl = (url) => {
    const patterns = [
        /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[a-zA-Z0-9_-]{11}/,
        /^[a-zA-Z0-9_-]{11}$/ // Solo ID
    ];
    return patterns.some(pattern => pattern.test(url));
};