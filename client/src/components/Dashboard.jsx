import React, { useState, useEffect } from 'react';
import { Search, Youtube, AlertTriangle, Heart, MessageCircle, TrendingUp, Shield, Eye, Users, BarChart3, PieChart, Activity, Trash2, Save, RefreshCw, ExternalLink } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Cell } from 'recharts';

const Dashboard = () => {
  const [url, setUrl] = useState('');
  const [maxComments, setMaxComments] = useState(100);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [savedVideos, setSavedVideos] = useState([]);

  const API_BASE = 'http://localhost:8000'; // Adjust to your FastAPI URL

  const toxicityLabels = {
    is_toxic: 'Toxic',
    is_hatespeech: 'Hate Speech',
    is_abusive: 'Abusive',
    is_provocative: 'Provocative',
    is_racist: 'Racist',
    is_obscene: 'Obscene',
    is_threat: 'Threat',
    is_religious_hate: 'Religious Hate',
    is_nationalist: 'Nationalist',
    is_sexist: 'Sexist',
    is_homophobic: 'Homophobic',
    is_radicalism: 'Radicalism'
  };

  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#84cc16', '#6366f1'];

  const analyzeVideo = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const videoId = getVideoIdFromUrl(url);
      console.log('Analyzing video ID:', videoId);
      
      const response = await fetch(`${API_BASE}/stats/?video_id=${videoId}&max_comments=${maxComments}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to analyze video: ${response.status}`);
      }

      const result = await response.json();
      console.log('API Response:', result);
      
      // Validar estructura de datos
      if (!result || typeof result !== 'object') {
        throw new Error('Invalid response format');
      }

      setData(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  const getVideoIdFromUrl = (url) => {
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return match ? match[1] : url;
  };

  const getTopComments = () => {
    if (!data?.comments || !Array.isArray(data.comments)) {
      console.log('No comments data available');
      return [];
    }
    
    try {
      return data.comments
        .filter(comment => comment && comment.like_count_comment && comment.like_count_comment > 0)
        .sort((a, b) => (b.like_count_comment || 0) - (a.like_count_comment || 0))
        .slice(0, 5);
    } catch (error) {
      console.error('Error processing top comments:', error);
      return [];
    }
  };

  const getToxicityLevel = () => {
    if (!data || !data.cantidad_comentarios) {
      console.log('No toxicity data available');
      return 'Unknown';
    }
    
    try {
      const totalComments = data.cantidad_comentarios || 0;
      const toxicCount = data.barras_toxicidad?.is_toxic?.true || 0;
      
      if (totalComments === 0) return 'No Data';
      
      const toxicityPercentage = (toxicCount / totalComments) * 100;
      
      if (toxicityPercentage > 30) return 'High';
      if (toxicityPercentage > 15) return 'Medium';
      if (toxicityPercentage > 5) return 'Low';
      return 'Very Low';
    } catch (error) {
      console.error('Error calculating toxicity level:', error);
      return 'Error';
    }
  };

  const getToxicityColor = () => {
    const level = getToxicityLevel();
    switch (level) {
      case 'High': return 'text-red-500';
      case 'Medium': return 'text-orange-500';
      case 'Low': return 'text-yellow-500';
      case 'Very Low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const prepareChartData = () => {
    if (!data?.barras_toxicidad || typeof data.barras_toxicidad !== 'object') {
      console.log('No chart data available');
      return [];
    }
    
    try {
      return Object.entries(data.barras_toxicidad).map(([key, value]) => {
        const trueCount = value?.true || 0;
        const falseCount = value?.false || 0;
        
        return {
          name: toxicityLabels[key] || key,
          toxic: trueCount,
          clean: falseCount,
          total: trueCount + falseCount
        };
      });
    } catch (error) {
      console.error('Error preparing chart data:', error);
      return [];
    }
  };

  const preparePieData = () => {
    if (!data?.sentimientos?.sentiment_types_distribution || typeof data.sentimientos.sentiment_types_distribution !== 'object') {
      console.log('No pie data available');
      return [];
    }
    
    try {
      return Object.entries(data.sentimientos.sentiment_types_distribution).map(([key, value]) => ({
        name: key.charAt(0).toUpperCase() + key.slice(1),
        value: value || 0
      }));
    } catch (error) {
      console.error('Error preparing pie data:', error);
      return [];
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <Youtube className="w-8 h-8 text-red-500" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">YouTube Toxicity Analyzer</h1>
                <p className="text-gray-400">Analyze comment sentiment and toxicity levels</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-white font-medium">Andre</p>
              <p className="text-gray-400 text-sm">Content Moderator</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Input Section */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-white/20">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Enter YouTube URL or Video ID"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-gray-300 text-sm">Max Comments:</span>
                <input
                  type="number"
                  value={maxComments}
                  onChange={(e) => setMaxComments(parseInt(e.target.value))}
                  className="w-20 px-3 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                />
              </div>
              <button
                onClick={analyzeVideo}
                disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Activity className="w-5 h-5" />}
                {loading ? 'Analyzing...' : 'Analyze Video'}
              </button>
            </div>
          </div>
          {error && (
            <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300">
              {error}
            </div>
          )}
        </div>

        {data && (
          <>
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-500/20 rounded-lg">
                    <MessageCircle className="w-6 h-6 text-blue-400" />
                  </div>
                  <span className="text-2xl font-bold text-white">{data.cantidad_comentarios}</span>
                </div>
                <h3 className="text-gray-300 font-medium">Total Comments</h3>
                <p className="text-gray-400 text-sm mt-1">Comments analyzed</p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-red-500/20 rounded-lg">
                    <AlertTriangle className="w-6 h-6 text-red-400" />
                  </div>
                  <span className={`text-2xl font-bold ${getToxicityColor()}`}>
                    {getToxicityLevel()}
                  </span>
                </div>
                <h3 className="text-gray-300 font-medium">Toxicity Level</h3>
                <p className="text-gray-400 text-sm mt-1">Overall assessment</p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-500/20 rounded-lg">
                    <Heart className="w-6 h-6 text-green-400" />
                  </div>
                  <span className="text-2xl font-bold text-white">{Math.round(data.mean_likes)}</span>
                </div>
                <h3 className="text-gray-300 font-medium">Avg. Likes</h3>
                <p className="text-gray-400 text-sm mt-1">Per comment</p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-purple-500/20 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-purple-400" />
                  </div>
                  <span className="text-2xl font-bold text-white">{Math.round(data.porcentaje_tagged)}%</span>
                </div>
                <h3 className="text-gray-300 font-medium">Tagged Content</h3>
                <p className="text-gray-400 text-sm mt-1">Flagged comments</p>
              </div>
            </div>

            {/* Tabs */}
            <div className="mb-8">
              <div className="flex flex-wrap gap-2 bg-white/10 backdrop-blur-sm rounded-2xl p-2 border border-white/20">
                {[
                  { id: 'overview', label: 'Overview', icon: BarChart3 },
                  { id: 'toxicity', label: 'Toxicity Analysis', icon: Shield },
                  { id: 'sentiment', label: 'Sentiment', icon: Heart },
                  { id: 'comments', label: 'Top Comments', icon: MessageCircle }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
                      activeTab === tab.id
                        ? 'bg-purple-500 text-white shadow-lg'
                        : 'text-gray-300 hover:bg-white/10'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                  <h3 className="text-white font-bold text-lg mb-4">Toxicity Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={prepareChartData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 12 }} angle={-45} textAnchor="end" />
                      <YAxis tick={{ fill: '#9CA3AF' }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px'
                        }}
                      />
                      <Bar dataKey="toxic" fill="#ef4444" />
                      <Bar dataKey="clean" fill="#22c55e" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                  <h3 className="text-white font-bold text-lg mb-4">Sentiment Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={preparePieData()}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {preparePieData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {activeTab === 'toxicity' && (
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <h3 className="text-white font-bold text-lg mb-6">Detailed Toxicity Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(data.barras_toxicidad || {}).map(([key, value]) => (
                    <div key={key} className="bg-white/5 rounded-xl p-4 border border-white/10">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300 font-medium">{toxicityLabels[key] || key}</span>
                        <span className="text-white font-bold">{value.true || 0}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-red-500 to-pink-500 h-2 rounded-full"
                          style={{
                            width: `${((value.true || 0) / ((value.true || 0) + (value.false || 0))) * 100}%`
                          }}
                        />
                      </div>
                      <p className="text-gray-400 text-sm mt-1">
                        {Math.round(((value.true || 0) / ((value.true || 0) + (value.false || 0))) * 100)}% of comments
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'sentiment' && (
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <h3 className="text-white font-bold text-lg mb-6">Sentiment Analysis</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-gray-300 font-medium mb-4">Average Sentiment Intensity</h4>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-white mb-2">
                        {data.sentimientos?.mean_sentiment_intensity?.toFixed(2) || 'N/A'}
                      </div>
                      <div className="text-gray-400">VADER Score (-1 to 1)</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-gray-300 font-medium mb-4">Sentiment Breakdown</h4>
                    <div className="space-y-3">
                      {Object.entries(data.sentimientos?.sentiment_types_distribution || {}).map(([sentiment, count]) => (
                        <div key={sentiment} className="flex justify-between items-center">
                          <span className="text-gray-300 capitalize">{sentiment}</span>
                          <span className="text-white font-bold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'comments' && (
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <h3 className="text-white font-bold text-lg mb-6">Top 5 Most Liked Comments</h3>
                <div className="space-y-4">
                  {getTopComments().map((comment, index) => (
                    <div key={index} className="bg-white/5 rounded-xl p-4 border border-white/10">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-gray-300 font-medium">{comment.author || 'Anonymous'}</span>
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-red-400" />
                          <span className="text-white font-bold">{comment.like_count_comment}</span>
                        </div>
                      </div>
                      <p className="text-gray-200 mb-3">{comment.text}</p>
                      <div className="flex flex-wrap gap-2">
                        {comment.is_toxic && (
                          <span className="px-2 py-1 bg-red-500/20 text-red-300 rounded-full text-xs">Toxic</span>
                        )}
                        {comment.is_hatespeech && (
                          <span className="px-2 py-1 bg-orange-500/20 text-orange-300 rounded-full text-xs">Hate Speech</span>
                        )}
                        {comment.is_abusive && (
                          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-xs">Abusive</span>
                        )}
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          comment.sentiment_type === 'positive' ? 'bg-green-500/20 text-green-300' :
                          comment.sentiment_type === 'negative' ? 'bg-red-500/20 text-red-300' :
                          'bg-gray-500/20 text-gray-300'
                        }`}>
                          {comment.sentiment_type || 'neutral'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center gap-4">
              <button className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl font-medium hover:from-green-600 hover:to-blue-600 flex items-center gap-2">
                <Save className="w-5 h-5" />
                Save Analysis
              </button>
              <button className="px-6 py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-medium hover:from-red-600 hover:to-pink-600 flex items-center gap-2">
                <Trash2 className="w-5 h-5" />
                Clear Data
              </button>
            </div>

            {/* Andre's Message */}
            <div className="mt-8 bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">A</span>
                </div>
                <div>
                  <h4 className="text-white font-bold">Andre published this analysis</h4>
                  <p className="text-gray-300 text-sm">Content moderation team</p>
                </div>
              </div>
              <p className="text-gray-200">
                "Analysis complete! This video shows a {getToxicityLevel().toLowerCase()} toxicity level with {data.cantidad_comentarios} comments analyzed. 
                The community engagement appears {data.mean_likes > 10 ? 'healthy' : 'moderate'} with an average of {Math.round(data.mean_likes)} likes per comment."
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;