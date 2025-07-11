import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  analyzeYouTubeVideo, 
  getSavedComments, 
  deleteSavedComments, 
  checkServerHealth,
  isValidYouTubeUrl,
  extractVideoIdFromUrl,
  formatToxicityDataForCharts,
  formatSentimentDataForCharts,
  getTopToxicComments,
  calculateEngagementMetrics
} from '../services/services';
import { 
  Play, 
  MessageCircle, 
  TrendingUp, 
  Save, 
  Trash2, 
  RefreshCw, 
  Eye, 
  AlertTriangle,
  Heart,
  Users,
  Link,
  Hash,
  Shield,
  Activity
} from 'lucide-react';

const LinkAnalysis = () => {
  const navigate = useNavigate();
  const [videoUrl, setVideoUrl] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [savedComments, setSavedComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [serverStatus, setServerStatus] = useState('unknown');
  const [activeTab, setActiveTab] = useState('input');
  const [maxComments, setMaxComments] = useState(100);

  // Verificar estado del servidor al cargar
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      await checkServerHealth();
      setServerStatus('online');
    } catch (error) {
      setServerStatus('offline');
    }
  };

 const handleAnalyze = async () => {
  if (!videoUrl.trim()) {
    setError('Por favor, ingresa una URL de YouTube válida');
    return;
  }

  if (!isValidYouTubeUrl(videoUrl)) {
    setError('La URL de YouTube no es válida');
    return;
  }

  setLoading(true);
  setError('');
  setAnalysisData({}); // Resetear datos anteriores

  try {
    console.log("Iniciando análisis..."); // Debug
    const data = await analyzeYouTubeVideo(videoUrl, maxComments);
    console.log("Datos recibidos:", data); // Debug
    if (!data) {
      throw new Error("No se recibieron datos del servidor");
    }
    // const videoId = extractVideoIdFromUrl(videoUrl);
    // navigate(`/statistics/${videoId}`);
    // if (!data) {
    //   throw new Error("No se recibieron datos del servidor");
    // }

    // Validación de estructura mínima
    if (!data.total_comments && !data.toxicity_stats) {
      console.warn("Datos incompletos recibidos:", data);
      throw new Error("Los datos recibidos están incompletos");
    }

    setAnalysisData({
      // Datos principales
      total_comments: data.total_comments || 0,
      
      // Toxicidad
      toxic_comments: data.toxicity_stats?.toxic_count || 
                     data.barras_toxicidad?.is_toxic?.true || 
                     0,
      general_toxicity_level: data.toxicity_stats?.average_toxicity ?
        `${Math.round(data.toxicity_stats.average_toxicity * 100)}%` : '0%',
      
      // Engagement
      avg_likes: data.engagement_stats?.mean_likes ??
        (data.comments && data.comments.length > 0
          ? data.comments.reduce((sum, c) => sum + (c.like_count || 0), 0) / data.comments.length
          : 0),
      
      // Datos completos para las secciones
      sentimientos: {
        sentiment_types_distribution: data.sentiment_distribution || 
                                    data.sentimientos?.sentiment_types_distribution || 
                                    { positive: 0, negative: 0, neutral: 0 }
      },
      barras_toxicidad: data.toxicity_stats || 
                       data.barras_toxicidad || 
                       { is_toxic: { true: 0, false: 0 } },
      engagement_stats: data.engagement_stats || {
        comments_with_urls: 0,
        url_percentage: 0,
        mean_likes: 0,
        total_likes: 0
      },
      comentarios: data.comments || []
    });

    setActiveTab('results');
  } catch (err) {
    console.error("Error en handleAnalyze:", err);
    setError(err.message || "Ocurrió un error al analizar el video");
    
    // Mostrar datos de debug en UI
    setAnalysisData({
      total_comments: 0,
      error: err.message,
      rawData: err.response?.data // Si usas axios
    });
  } finally {
    setLoading(false);
  }
};

  const handleGetSavedComments = async () => {
    if (!videoUrl.trim()) {
      setError('Por favor, ingresa una URL de YouTube para buscar comentarios guardados');
      return;
    }

    const videoId = extractVideoIdFromUrl(videoUrl);
    setLoading(true);
    setError('');

    try {
      const data = await getSavedComments(videoId);
      setSavedComments(data.comments || []);
      setActiveTab('saved');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSavedComments = async () => {
    if (!videoUrl.trim()) {
      setError('Por favor, ingresa una URL de YouTube');
      return;
    }

    const videoId = extractVideoIdFromUrl(videoUrl);
    setLoading(true);
    setError('');

    try {
      await deleteSavedComments(videoId);
      setSavedComments([]);
      alert('Comentarios eliminados exitosamente');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getToxicityLevel = (probability) => {
    if (probability >= 0.7) return { label: 'Alto', color: 'bg-red-500', textColor: 'text-red-500' };
    if (probability >= 0.4) return { label: 'Medio', color: 'bg-yellow-500', textColor: 'text-yellow-500' };
    return { label: 'Bajo', color: 'bg-green-500', textColor: 'text-green-500' };
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      'positive': 'text-green-600 bg-green-100',
      'negative': 'text-red-600 bg-red-100',
      'neutral': 'text-gray-600 bg-gray-100',
      'compound': 'text-blue-600 bg-blue-100'
    };
    return colors[sentiment?.toLowerCase()] || 'text-gray-600 bg-gray-100';
  };

  const getSentimentIcon = (sentiment) => {
    const icons = {
      'positive': '😊',
      'negative': '😞',
      'neutral': '😐'
    };
    return icons[sentiment?.toLowerCase()] || '🤔';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-red-600 mb-2">
            YouTube Video Analysis
          </h1>
          <p className="text-gray-600">
            Analiza sentimientos y toxicidad en comentarios de YouTube
          </p>
          
          {/* Server Status */}
          <div className="mt-4 flex justify-center">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              serverStatus === 'online' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-red-100 text-red-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                serverStatus === 'online' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              Servidor: {serverStatus === 'online' ? 'En línea' : 'Desconectado'}
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap justify-center mb-8 bg-white rounded-lg shadow-md p-2">
          {[
            { id: 'input', label: 'Análisis', icon: Play },
            { id: 'results', label: 'Resultados', icon: TrendingUp },
            { id: 'saved', label: 'Guardados', icon: Save }
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  if (tab.id === 'results') {
                    const videoId = extractVideoIdFromUrl(videoUrl);
                    if (videoId) {
                      navigate(`/statistics/${videoId}`);
                    } else {
                      // Manejar el caso cuando no hay videoId válido
                      console.error("URL de video no válida");
                    }
                  } else {
                    setActiveTab(tab.id);
                  }
                }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-red-500 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            <div className="flex items-center gap-2">
              <AlertTriangle size={20} />
              {error}
            </div>
          </div>
        )}

        {/* Input Tab */}
        {activeTab === 'input' && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Play className="text-red-500" />
              Configurar Análisis
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL del Video de YouTube
                </label>
                <input
                  type="text"
                  placeholder="https://www.youtube.com/watch?v=VIDEO_ID o solo VIDEO_ID"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número máximo de comentarios a analizar
                </label>
                <select
                  value={maxComments}
                  onChange={(e) => setMaxComments(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value={50}>50 comentarios</option>
                  <option value={100}>100 comentarios</option>
                  <option value={200}>200 comentarios</option>
                  <option value={500}>500 comentarios</option>
                </select>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="flex-1 bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <RefreshCw className="animate-spin" size={20} />
                  ) : (
                    <Play size={20} />
                  )}
                  {loading ? 'Analizando...' : 'Analizar Video'}
                </button>

                <button
                  onClick={handleGetSavedComments}
                  disabled={loading}
                  className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
                >
                  <Eye size={20} />
                  Ver Guardados
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && analysisData && (
          <div className="space-y-6">
            {/* Video Info */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <TrendingUp className="text-green-500" />
                Información del Video
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <MessageCircle className="mx-auto mb-2 text-blue-500" size={24} />
                  <p className="text-sm text-gray-600">Total Comentarios</p>
                  <p className="text-2xl font-bold">{analysisData.total_comments}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <AlertTriangle className="mx-auto mb-2 text-red-500" size={24} />
                  <p className="text-sm text-gray-600">Comentarios Tóxicos</p>
                  <p className="text-2xl font-bold">{analysisData.toxic_comments}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <Heart className="mx-auto mb-2 text-pink-500" size={24} />
                  <p className="text-sm text-gray-600">Promedio Likes</p>
                  <p className="text-2xl font-bold">{analysisData.avg_likes}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <Shield className="mx-auto mb-2 text-purple-500" size={24} />
                  <p className="text-sm text-gray-600">Nivel General</p>
                  <p className="text-2xl font-bold">{analysisData.general_toxicity_level}</p>
                </div>
              </div>
            </div>

            {/* Sentiment Analysis */}
            {analysisData.sentimientos && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Activity className="text-blue-500" />
                  Análisis de Sentimientos
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {Object.entries(analysisData.sentimientos.sentiment_types_distribution || {}).map(([sentiment, count]) => (
                    <div key={sentiment} className="bg-gray-50 p-4 rounded-lg text-center">
                      <div className="text-2xl mb-2">
                        {getSentimentIcon(sentiment)}
                      </div>
                      <p className="font-medium capitalize">{sentiment}</p>
                      <p className="text-2xl font-bold">{count}</p>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(sentiment)}`}>
                        {((count / analysisData.total_comments) * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Toxicity Analysis */}
            {analysisData.barras_toxicidad && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <AlertTriangle className="text-red-500" />
                  Análisis de Toxicidad
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(analysisData.barras_toxicidad).map(([type, data]) => {
                    const total = data.true + data.false;
                    const percentage = total > 0 ? ((data.true / total) * 100).toFixed(1) : 0;
                    
                    return (
                      <div key={type} className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium mb-2 capitalize">
                          {type.replace('is_', '').replace('_', ' ')}
                        </h4>
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-red-600">Detectado: {data.true}</span>
                          <span className="text-green-600">Limpio: {data.false}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-red-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{percentage}% tóxico</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Engagement Stats */}
            {analysisData.engagement_stats && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Users className="text-purple-500" />
                  Estadísticas de Engagement
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <Link className="mx-auto mb-2 text-blue-500" size={24} />
                    <p className="text-sm text-gray-600">Comentarios con URLs</p>
                    <p className="text-2xl font-bold">{analysisData.engagement_stats.comments_with_urls}</p>
                    <p className="text-xs text-gray-500">{analysisData.engagement_stats.url_percentage}%</p>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <Hash className="mx-auto mb-2 text-green-500" size={24} />
                    <p className="text-sm text-gray-600">Comentarios con Tags</p>
                    <p className="text-2xl font-bold">{analysisData.engagement_stats.comments_with_tags}</p>
                    <p className="text-xs text-gray-500">{analysisData.engagement_stats.tag_percentage}%</p>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <Heart className="mx-auto mb-2 text-pink-500" size={24} />
                    <p className="text-sm text-gray-600">Likes Totales</p>
                    <p className="text-2xl font-bold">{analysisData.engagement_stats.total_likes}</p>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <TrendingUp className="mx-auto mb-2 text-orange-500" size={24} />
                    <p className="text-sm text-gray-600">Engagement Rate</p>
                    <p className="text-2xl font-bold">{analysisData.engagement_stats.engagement_rate}%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Top Toxic Comments */}
            {analysisData.comentarios && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <AlertTriangle className="text-red-500" />
                  Comentarios Más Tóxicos
                </h3>
                
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {getTopToxicComments(analysisData.comentarios, 10).map((comment, index) => {
                    const toxicityLevel = getToxicityLevel(comment.toxic_probability);
                    
                    return (
                      <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start mb-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${toxicityLevel.color} text-white`}>
                            {toxicityLevel.label} ({(comment.toxic_probability * 100).toFixed(1)}%)
                          </span>
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Heart size={14} />
                            {comment.like_count || 0}
                          </div>
                        </div>
                        <p className="text-sm text-gray-700">{comment.text}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Saved Comments Tab */}
        {activeTab === 'saved' && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Save className="text-purple-500" />
                Comentarios Guardados
              </h2>
              
              {savedComments.length > 0 && (
                <button
                  onClick={handleDeleteSavedComments}
                  className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center gap-2"
                >
                  <Trash2 size={16} />
                  Eliminar Todos
                </button>
              )}
            </div>

            {savedComments.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {savedComments.map((comment, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-700">{comment}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Save size={48} className="mx-auto mb-4 opacity-50" />
                <p>No hay comentarios guardados para este video.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LinkAnalysis;