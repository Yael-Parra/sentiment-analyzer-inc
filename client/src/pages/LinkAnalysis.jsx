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
  Activity,
  ThumbsUp,
  Zap,
  BarChart3,
  CheckCircle,
  Clock,
  Wifi,
  WifiOff
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

  // Función para formatear números grandes
  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

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
    setError('Please enter a valid YouTube URL');
    return;
  }

  if (!isValidYouTubeUrl(videoUrl)) {
    setError('The YouTube URL is not valid');
    return;
  }

  setLoading(true);
  setError('');
  setAnalysisData({}); // Resetear datos anteriores

  try {
    console.log("Starting analysis..."); // Debug
    const data = await analyzeYouTubeVideo(videoUrl, maxComments);
    console.log("Data received:", data); // Debug
    if (!data) {
      throw new Error("No data received from server");
    }

    // Validación de estructura mínima
    if (!data.total_comments && !data.toxicity_stats) {
      console.warn("Incomplete data received:", data);
      throw new Error("The received data is incomplete");
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
        total_likes: 0,
        // Nuevos campos del video
        video_likes_total: 0,
        video_views_total: 0,
        video_comments_total: 0
      },
      comentarios: data.comments || []
    });

    setActiveTab('results');
  } catch (err) {
    console.error("Error in handleAnalyze:", err);
    setError(err.message || "An error occurred while analyzing the video");
    
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
      setError('Please enter a YouTube URL to search for saved comments');
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
      setError('Please enter a YouTube URL');
      return;
    }

    const videoId = extractVideoIdFromUrl(videoUrl);
    setLoading(true);
    setError('');

    try {
      await deleteSavedComments(videoId);
      setSavedComments([]);
      alert('Comments deleted successfully');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getToxicityLevel = (probability) => {
    if (probability >= 0.7) return { label: 'High', color: 'bg-red-500', textColor: 'text-red-500' };
    if (probability >= 0.4) return { label: 'Medium', color: 'bg-yellow-500', textColor: 'text-yellow-500' };
    return { label: 'Low', color: 'bg-green-500', textColor: 'text-green-500' };
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
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-pink-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-red-100 text-red-600 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <Zap size={16} />
            AI-Powered Analysis
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
            YouTube Video <span className="text-red-500">Analysis</span>
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Analyze sentiment and toxicity in YouTube comments with advanced AI
          </p>
          
          {/* Server Status */}
          <div className="mt-6 flex justify-center">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium shadow-sm ${
              serverStatus === 'online' 
                ? 'bg-green-100 text-green-700 border border-green-200' 
                : 'bg-red-100 text-red-700 border border-red-200'
            }`}>
              {serverStatus === 'online' ? <Wifi size={16} /> : <WifiOff size={16} />}
              Server: {serverStatus === 'online' ? 'Online' : 'Offline'}
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap justify-center mb-8">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-2 border border-white/20">
            {[
              { id: 'input', label: 'Analysis', icon: Play, color: 'text-blue-500' },
              { id: 'results', label: 'Results', icon: BarChart3, color: 'text-green-500' }
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
                        console.error("Invalid video URL");
                      }
                    } else {
                      setActiveTab(tab.id);
                    }
                  }}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300 font-medium ${
                    activeTab === tab.id
                      ? 'bg-red-500 text-white shadow-lg transform scale-105'
                      : 'text-gray-600 hover:bg-white/50 hover:text-red-500'
                  }`}
                >
                  <Icon size={18} className={activeTab !== tab.id ? tab.color : ''} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl mb-8 shadow-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle size={20} className="text-red-500" />
              <span className="font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Input Tab */}
        {activeTab === 'input' && (
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 mb-8 border border-white/20">
            <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-xl">
                <Play className="text-red-500" size={24} />
              </div>
              Configure Analysis
            </h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  YouTube Video URL
                </label>
                <input
                  type="text"
                  placeholder="https://www.youtube.com/watch?v=VIDEO_ID or just VIDEO_ID"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  className="w-full px-6 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-red-100 focus:border-red-500 transition-all duration-300 text-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Maximum number of comments to analyze
                </label>
                <select
                  value={maxComments}
                  onChange={(e) => setMaxComments(Number(e.target.value))}
                  className="w-full px-6 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-red-100 focus:border-red-500 transition-all duration-300 text-lg"
                >
                  <option value={50}>50 comments</option>
                  <option value={100}>100 comments</option>
                  <option value={200}>200 comments</option>
                  <option value={500}>500 comments</option>
                </select>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="flex-1 bg-gradient-to-r from-red-500 to-pink-600 text-white px-8 py-4 rounded-2xl hover:from-red-600 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 font-semibold text-lg"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="animate-spin" size={24} />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Play size={24} />
                      Start Analysis
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && analysisData && (
          <div className="space-y-8">
            {/* Video Info */}
            <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-xl">
                  <TrendingUp className="text-green-500" size={24} />
                </div>
                Video Information
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-2xl text-center border border-blue-200 hover:shadow-lg transition-all duration-300">
                  <MessageCircle className="mx-auto mb-3 text-blue-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Total Comments</p>
                  <p className="text-3xl font-bold text-blue-700">{analysisData.total_comments}</p>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-2xl text-center border border-red-200 hover:shadow-lg transition-all duration-300">
                  <AlertTriangle className="mx-auto mb-3 text-red-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Toxic Comments</p>
                  <p className="text-3xl font-bold text-red-700">{analysisData.toxic_comments}</p>
                </div>

                <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-6 rounded-2xl text-center border border-pink-200 hover:shadow-lg transition-all duration-300">
                  <Heart className="mx-auto mb-3 text-pink-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Average Likes</p>
                  <p className="text-3xl font-bold text-pink-700">{Math.round(analysisData.avg_likes)}</p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-2xl text-center border border-purple-200 hover:shadow-lg transition-all duration-300">
                  <Shield className="mx-auto mb-3 text-purple-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">General Level</p>
                  <p className="text-3xl font-bold text-purple-700">{analysisData.general_toxicity_level}</p>
                </div>
              </div>
            </div>

            {/* Sentiment Analysis */}
            {analysisData.sentimientos && (
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-xl">
                    <Activity className="text-blue-500" size={24} />
                  </div>
                  Sentiment Analysis
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Object.entries(analysisData.sentimientos.sentiment_types_distribution || {}).map(([sentiment, count]) => (
                    <div key={sentiment} className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                      <div className="text-4xl mb-3">
                        {getSentimentIcon(sentiment)}
                      </div>
                      <p className="font-semibold capitalize text-lg text-gray-700">{sentiment}</p>
                      <p className="text-3xl font-bold text-gray-800 my-2">{count}</p>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getSentimentColor(sentiment)}`}>
                        {((count / analysisData.total_comments) * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Toxicity Analysis */}
            {analysisData.barras_toxicidad && (
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-xl">
                    <AlertTriangle className="text-red-500" size={24} />
                  </div>
                  Toxicity Analysis
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(analysisData.barras_toxicidad).map(([type, data]) => {
                    const total = data.true + data.false;
                    const percentage = total > 0 ? ((data.true / total) * 100).toFixed(1) : 0;
                    
                    return (
                      <div key={type} className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl border hover:shadow-lg transition-all duration-300">
                        <h4 className="font-semibold mb-3 capitalize text-lg text-gray-700">
                          {type.replace('is_', '').replace('_', ' ')}
                        </h4>
                        <div className="flex justify-between text-sm mb-3">
                          <span className="text-red-600 font-medium">Detected: {data.true}</span>
                          <span className="text-green-600 font-medium">Clean: {data.false}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                          <div
                            className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <p className="text-sm text-gray-600 font-medium">{percentage}% toxic</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Engagement Stats - SECCIÓN MEJORADA */}
            {analysisData.engagement_stats && (
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-xl">
                    <Users className="text-purple-500" size={24} />
                  </div>
                  Engagement Statistics
                </h3>
                
                {/* Estadísticas del Video */}
                <div className="mb-8">
                  <h4 className="text-xl font-semibold mb-4 text-gray-700">Video Statistics</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-2xl text-center border border-green-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                      <ThumbsUp className="mx-auto mb-3 text-green-600" size={32} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Video Likes</p>
                      <p className="text-3xl font-bold text-green-700">
                        {formatNumber(analysisData.engagement_stats.video_likes_total)}
                      </p>
                    </div>

                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-2xl text-center border border-blue-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                      <Eye className="mx-auto mb-3 text-blue-600" size={32} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Views</p>
                      <p className="text-3xl font-bold text-blue-700">
                        {formatNumber(analysisData.engagement_stats.video_views_total)}
                      </p>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-2xl text-center border border-purple-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                      <MessageCircle className="mx-auto mb-3 text-purple-600" size={32} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Video Comments</p>
                      <p className="text-3xl font-bold text-purple-700">
                        {formatNumber(analysisData.engagement_stats.video_comments_total)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Estadísticas de Comentarios Analizados */}
                <div>
                  <h4 className="text-xl font-semibold mb-4 text-gray-700">Analyzed Comments</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border hover:shadow-lg transition-all duration-300">
                      <Link className="mx-auto mb-3 text-blue-500" size={28} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Comments with URLs</p>
                      <p className="text-2xl font-bold text-gray-800">{analysisData.engagement_stats.comments_with_urls}</p>
                      <p className="text-xs text-gray-500 font-medium">{analysisData.engagement_stats.url_percentage}%</p>
                    </div>

                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border hover:shadow-lg transition-all duration-300">
                      <Hash className="mx-auto mb-3 text-green-500" size={28} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Comments with Tags</p>
                      <p className="text-2xl font-bold text-gray-800">{analysisData.engagement_stats.comments_with_tags}</p>
                      <p className="text-xs text-gray-500 font-medium">{analysisData.engagement_stats.tag_percentage}%</p>
                    </div>

                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border hover:shadow-lg transition-all duration-300">
                      <Heart className="mx-auto mb-3 text-pink-500" size={28} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Comment Likes</p>
                      <p className="text-2xl font-bold text-gray-800">{formatNumber(analysisData.engagement_stats.total_likes)}</p>
                    </div>

                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border hover:shadow-lg transition-all duration-300">
                      <TrendingUp className="mx-auto mb-3 text-orange-500" size={28} />
                      <p className="text-sm font-semibold text-gray-600 mb-1">Engagement Rate</p>
                      <p className="text-2xl font-bold text-gray-800">{analysisData.engagement_stats.engagement_rate}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Top Toxic Comments */}
            {analysisData.comentarios && (
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-xl">
                    <AlertTriangle className="text-red-500" size={24} />
                  </div>
                  Most Toxic Comments
                </h3>
                
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {getTopToxicComments(analysisData.comentarios, 10).map((comment, index) => {
                    const toxicityLevel = getToxicityLevel(comment.toxic_probability);
                    
                    return (
                      <div key={index} className="border border-gray-200 rounded-2xl p-6 hover:bg-gray-50 transition-all duration-300 hover:shadow-lg">
                        <div className="flex justify-between items-start mb-3">
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${toxicityLevel.color} text-white shadow-sm`}>
                            {toxicityLevel.label} ({(comment.toxic_probability * 100).toFixed(1)}%)
                          </span>
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Heart size={16} />
                            <span className="font-medium">{comment.like_count || 0}</span>
                          </div>
                        </div>
                        <p className="text-gray-700 leading-relaxed">{comment.text}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LinkAnalysis;