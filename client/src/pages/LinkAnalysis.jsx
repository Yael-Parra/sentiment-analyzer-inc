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

  // Función helper para obtener likes de un comentario
  const getCommentLikes = (comment) => {
    return comment?.total_likes_comment || comment?.like_count || comment?.likes || 0;
  };

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

      // Calcular sentimientos directamente desde comentarios
      const sentimentDistribution = { positive: 0, negative: 0, neutral: 0 };
      
      if (data.comments && Array.isArray(data.comments)) {
        data.comments.forEach(comment => {
          if (comment?.sentiment_type) {
            const sentiment = comment.sentiment_type.toLowerCase();
            if (sentiment === 'positive') sentimentDistribution.positive++;
            else if (sentiment === 'negative') sentimentDistribution.negative++;
            else if (sentiment === 'neutral') sentimentDistribution.neutral++;
          }
        });
      }

      // Extraer datos de toxicidad desde stats
      const toxicityStats = data.stats || {};

      // Calcular total de likes de comentarios - usando helper
      const totalCommentLikes = data.comments ? 
        data.comments.reduce((sum, c) => sum + getCommentLikes(c), 0) : 0;

      // Calcular promedio de likes
      const avgLikes = data.comments && data.comments.length > 0 ?
        totalCommentLikes / data.comments.length : 0;

      console.log("📊 Sentiment calculated:", sentimentDistribution);
      console.log("📊 Toxicity from stats:", toxicityStats);
      console.log("📊 Total comment likes:", totalCommentLikes);
      console.log("📊 Sample comment with likes:", data.comments?.[0]);
      console.log("📊 First 3 comments likes:", data.comments?.slice(0, 3).map(c => ({ 
        text: c.text?.substring(0, 50) + '...', 
        total_likes_comment: c.total_likes_comment,
        like_count: c.like_count,
        allKeys: Object.keys(c)
      })));

      setAnalysisData({
        // Datos principales
        total_comments: data.total_comments || 0,
        
        // Toxicidad - desde stats
        toxic_comments: toxicityStats.is_toxic?.true || 0,
        general_toxicity_level: data.total_comments > 0 ?
          `${Math.round((toxicityStats.is_toxic?.true || 0) / data.total_comments * 100)}%` : '0%',
        
        // Engagement - usando total_likes_comment
        avg_likes: avgLikes,
        
        // Datos de sentimientos - calculados desde comentarios
        sentimientos: {
          sentiment_types_distribution: sentimentDistribution
        },
        
        // Datos de toxicidad - desde stats
        barras_toxicidad: toxicityStats,
        
        // Engagement stats mejorado
        engagement_stats: {
          mean_likes: avgLikes,
          total_likes: totalCommentLikes,
          video_comments_total: data.total_comments || 0,
          comments_with_urls: 0,
          url_percentage: 0,
          comments_with_tags: 0,
          tag_percentage: 0,
          engagement_rate: 0,
          video_likes_total: 0,
          video_views_total: 0
        },
        
        comentarios: data.comments || []
      });

      setActiveTab('results');
    } catch (err) {
      console.error("Error in handleAnalyze:", err);
      setError(err.message || "An error occurred while analyzing the video");
      
      setAnalysisData({
        total_comments: 0,
        error: err.message,
        rawData: err.response?.data
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
      'neutral': 'text-gray-600 bg-gray-100'
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
    <div className="min-h-screen" style={{ backgroundColor: '#F7FAFC' }}>
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
                  className="flex-1 bg-gradient-to-r from-red-500 to-red-700 text-white px-8 py-4 rounded-2xl hover:from-red-600 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 font-semibold text-lg"
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
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-2xl text-center border border-blue-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <MessageCircle className="mx-auto mb-3 text-blue-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Total Comments</p>
                  <p className="text-3xl font-bold text-blue-700">{analysisData.total_comments}</p>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-2xl text-center border border-red-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <AlertTriangle className="mx-auto mb-3 text-red-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Toxic Comments</p>
                  <p className="text-3xl font-bold text-red-700">{analysisData.toxic_comments}</p>
                </div>

                <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-6 rounded-2xl text-center border border-pink-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <Heart className="mx-auto mb-3 text-pink-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Average Likes</p>
                  <p className="text-3xl font-bold text-pink-700">{Math.round(analysisData.avg_likes)}</p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-2xl text-center border border-purple-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <Shield className="mx-auto mb-3 text-purple-500" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Toxicity Level</p>
                  <p className="text-3xl font-bold text-purple-700">{analysisData.general_toxicity_level}</p>
                </div>
              </div>
            </div>

            {/* Nueva Card: Total de Likes de Comentarios */}
            <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20">
              <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <div className="p-2 bg-pink-100 rounded-xl">
                  <Heart className="text-pink-500" size={24} />
                </div>
                Comment Engagement
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-6 rounded-2xl text-center border border-pink-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <ThumbsUp className="mx-auto mb-3 text-pink-600" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Total Comment Likes</p>
                  <p className="text-3xl font-bold text-pink-700">
                    {formatNumber(analysisData.engagement_stats?.total_likes || 0)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">From {analysisData.total_comments} comments</p>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-2xl text-center border border-orange-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <TrendingUp className="mx-auto mb-3 text-orange-600" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Average Likes per Comment</p>
                  <p className="text-3xl font-bold text-orange-700">
                    {Math.round(analysisData.avg_likes || 0)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Likes per comment</p>
                </div>

                <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-6 rounded-2xl text-center border border-indigo-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                  <Activity className="mx-auto mb-3 text-indigo-600" size={32} />
                  <p className="text-sm font-semibold text-gray-600 mb-1">Engagement Rate</p>
                  <p className="text-3xl font-bold text-indigo-700">
                    {analysisData.total_comments > 0 ? 
                      ((analysisData.engagement_stats?.total_likes || 0) / analysisData.total_comments * 100).toFixed(1) : 0}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Likes to comments ratio</p>
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
                  {/* Positive Sentiment */}
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-2xl text-center border border-green-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                    <div className="text-4xl mb-3">😊</div>
                    <p className="font-semibold text-lg text-gray-700">Positive</p>
                    <p className="text-4xl font-bold text-gray-800 my-2">
                      {analysisData.sentimientos.sentiment_types_distribution?.positive || 0}
                    </p>
                    <span className="inline-block px-3 py-1 rounded-full text-sm font-semibold text-green-600 bg-green-100">
                      {analysisData.total_comments > 0 
                        ? (((analysisData.sentimientos.sentiment_types_distribution?.positive || 0) / analysisData.total_comments) * 100).toFixed(1) 
                        : 0}%
                    </span>
                  </div>

                  {/* Negative Sentiment */}
                  <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-2xl text-center border border-red-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                    <div className="text-4xl mb-3">😞</div>
                    <p className="font-semibold text-lg text-gray-700">Negative</p>
                    <p className="text-4xl font-bold text-gray-800 my-2">
                      {analysisData.sentimientos.sentiment_types_distribution?.negative || 0}
                    </p>
                    <span className="inline-block px-3 py-1 rounded-full text-sm font-semibold text-red-600 bg-red-100">
                      {analysisData.total_comments > 0 
                        ? (((analysisData.sentimientos.sentiment_types_distribution?.negative || 0) / analysisData.total_comments) * 100).toFixed(1) 
                        : 0}%
                    </span>
                  </div>

                  {/* Neutral Sentiment */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl text-center border border-gray-200 hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                    <div className="text-4xl mb-3">😐</div>
                    <p className="font-semibold text-lg text-gray-700">Neutral</p>
                    <p className="text-4xl font-bold text-gray-800 my-2">
                      {analysisData.sentimientos.sentiment_types_distribution?.neutral || 0}
                    </p>
                    <span className="inline-block px-3 py-1 rounded-full text-sm font-semibold text-gray-600 bg-gray-100">
                      {analysisData.total_comments > 0 
                        ? (((analysisData.sentimientos.sentiment_types_distribution?.neutral || 0) / analysisData.total_comments) * 100).toFixed(1) 
                        : 0}%
                    </span>
                  </div>
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
                    if (!data || typeof data !== 'object' || (!data.true && !data.false)) return null;
                    
                    const total = (data.true || 0) + (data.false || 0);
                    const percentage = total > 0 ? (((data.true || 0) / total) * 100).toFixed(1) : 0;
                    
                    return (
                      <div key={type} className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-2xl border hover:shadow-lg transition-all duration-300 transform hover:scale-105">
                        <h4 className="font-semibold mb-3 capitalize text-lg text-gray-700">
                          {type.replace('is_', '').replace('_', ' ')}
                        </h4>
                        <div className="flex justify-between text-sm mb-3">
                          <span className="text-red-600 font-medium">Detected: {data.true || 0}</span>
                          <span className="text-green-600 font-medium">Clean: {data.false || 0}</span>
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
                      <div key={index} className="border border-gray-200 rounded-2xl p-6 hover:bg-gray-50 transition-all duration-300 hover:shadow-lg transform hover:scale-[1.02]">
                        <div className="flex justify-between items-start mb-3">
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${toxicityLevel.color} text-white shadow-sm`}>
                            {toxicityLevel.label} ({(comment.toxic_probability * 100).toFixed(1)}%)
                          </span>
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Heart size={16} />
                            <span className="font-medium">{formatNumber(getCommentLikes(comment))} likes</span>
                          </div>
                        </div>
                        <p className="text-gray-700 leading-relaxed">{comment.text}</p>
                        
                        {/* Información adicional del comentario */}
                        <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            {comment.sentiment_type && (
                              <span className={`px-2 py-1 rounded-full ${getSentimentColor(comment.sentiment_type)}`}>
                                {getSentimentIcon(comment.sentiment_type)} {comment.sentiment_type}
                              </span>
                            )}
                            {comment.author && (
                              <span className="flex items-center gap-1">
                                <Users size={12} />
                                {comment.author}
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-1 text-sm font-medium text-pink-600 bg-pink-50 px-2 py-1 rounded-full">
                            <ThumbsUp size={14} />
                            {formatNumber(getCommentLikes(comment))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Call to Action para ir a Statistics */}
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl shadow-2xl p-8 border border-white/20 text-center">
              <h3 className="text-2xl font-bold text-white mb-4">Want More Detailed Analytics?</h3>
              <p className="text-indigo-100 mb-6">Get comprehensive charts, advanced metrics, and interactive visualizations</p>
              <button
                onClick={() => {
                  const videoId = extractVideoIdFromUrl(videoUrl);
                  if (videoId) {
                    navigate(`/statistics/${videoId}`);
                  }
                }}
                className="bg-white text-indigo-600 px-8 py-4 rounded-2xl font-semibold hover:bg-gray-50 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center gap-3 mx-auto"
              >
                <BarChart3 size={24} />
                View Advanced Statistics
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LinkAnalysis;