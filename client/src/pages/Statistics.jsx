import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getVideoStatistics,
  formatToxicityDataForCharts,
  formatSentimentDataForCharts,
  calculateEngagementMetrics,
  getTopToxicComments
} from '../services/services';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import html2pdf from 'html2pdf.js';

const Statistics = () => {
  const { videoId } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [topN, setTopN] = useState(5);
  const [filters, setFilters] = useState({
    dateRange: 'all',
    toxicityThreshold: 0.5,
    sentiment: 'all'
  });
  const reportRef = useRef();

  const getToxicityColor = (toxicity) => {
    const hue = (1 - toxicity) * 120;
    return `hsl(${hue}, 100%, 50%)`;
  };

  const getSentimentColor = (sentiment) => {
    switch(sentiment.toLowerCase()) {
      case 'positive': return '#10B981';
      case 'negative': return '#EF4444';
      case 'neutral': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  useEffect(() => {
    console.log("Video ID from URL:", videoId);
    
    if (!videoId || videoId === "undefined") {
      setError("No se proporcionó un ID de video válido");
      setLoading(false);
      navigate("/");
      return;
    }

    const fetchStats = async () => {
      try {
        console.log("Fetching stats for video:", videoId);
        const data = await getVideoStatistics(videoId);
        
        if (!data) {
          throw new Error("No se recibieron datos del servidor");
        }
        
        console.log("Data received:", data);
        setStats(data);
      } catch (err) {
        console.error("Error fetching stats:", err);
        setError(err.message || "Error al cargar estadísticas");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [videoId, navigate]);
  
  if (loading) return <div className="text-center py-20">Cargando estadísticas...</div>;
  if (error) return <div className="text-red-500 text-center py-20">Error: {error}</div>;
  if (!stats) return <div className="text-center py-20">No hay datos disponibles</div>;

  // Format data for charts based on your backend structure
  const toxicityData = formatToxicityDataForCharts(stats.toxicity_stats);
  const sentimentData = formatSentimentDataForCharts(stats.sentiment_distribution);
  const engagementMetrics = calculateEngagementMetrics(stats);
  
  // Get comments and format toxicity over time
  const toxicityOverTime = stats.comments?.map(comment => ({
    time: new Date(comment.published_at_comment || comment.created_at).toLocaleDateString(),
    toxicity: Math.round((comment.toxic_probability || 0) * 100)
  })) || [];

  const topToxicComments = getTopToxicComments(stats.comments || []);

  const handleDownloadPDF = () => {
    const opt = {
      margin: 0.5,
      filename: `estadisticas_video_${videoId}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(reportRef.current).save();
  };

  return (
    <div ref={reportRef} className="container mx-auto px-4 py-8 bg-gray-50">
      {/* Header with title and download button */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">
          Análisis de Comentarios - Video {videoId}
        </h1>
        <button
          onClick={handleDownloadPDF}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-md transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Exportar Reporte
        </button>
      </div>

      {/* Navigation tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['overview', 'toxicity', 'sentiment', 'engagement'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'overview' && 'Resumen'}
              {tab === 'toxicity' && 'Toxicidad'}
              {tab === 'sentiment' && 'Sentimiento'}
              {tab === 'engagement' && 'Engagement'}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <h3 className="font-medium text-gray-700 mb-3">Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rango de fechas</label>
            <select 
              value={filters.dateRange}
              onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todo el período</option>
              <option value="week">Última semana</option>
              <option value="month">Último mes</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Umbral de toxicidad</label>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.1"
              value={filters.toxicityThreshold}
              onChange={(e) => setFilters({...filters, toxicityThreshold: parseFloat(e.target.value)})}
              className="w-full"
            />
            <span className="text-sm text-gray-600">{Math.round(filters.toxicityThreshold * 100)}%</span>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sentimiento</label>
            <select 
              value={filters.sentiment}
              onChange={(e) => setFilters({...filters, sentiment: e.target.value})}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todos</option>
              <option value="positive">Positivo</option>
              <option value="negative">Negativo</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Comments card */}
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-700">Comentarios</h3>
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold mt-4 text-gray-900">{stats.total_comments}</p>
          <p className="text-sm text-gray-500 mt-2">Analizados</p>
        </div>

        {/* Toxicity card */}
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-700">Toxicidad</h3>
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold mt-4 text-gray-900">
            {Math.round((stats.toxicity_stats?.average_toxicity || 0) * 100)}%
          </p>
          <p className="text-sm text-gray-500 mt-2">Promedio</p>
        </div>
        
        {/* Toxicity over time card */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 flex items-center gap-2">
            <span className="w-2 h-6 bg-yellow-500 rounded-full"></span>
            Toxicidad a lo Largo del Tiempo
          </h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={toxicityOverTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="toxicity" stroke="#ef4444" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment card */}
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-700">Sentimiento</h3>
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold mt-4 text-gray-900 capitalize">
            {stats.sentiment_distribution?.dominant_sentiment || 'neutral'}
          </p>
          <p className="text-sm text-gray-500 mt-2">Dominante</p>
        </div>

        {/* Engagement card */}
        <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-700">Engagement</h3>
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold mt-4 text-gray-900">
            {engagementMetrics.maxLikes || 0}
          </p>
          <p className="text-sm text-gray-500 mt-2">Máx. likes</p>
        </div>
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Toxicity chart */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 flex items-center gap-2">
            <span className="w-2 h-6 bg-red-500 rounded-full"></span>
            Distribución de Toxicidad
          </h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={toxicityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="type" tick={{ fill: '#6b7280' }} />
                <YAxis tick={{ fill: '#6b7280' }} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar dataKey="toxic" name="Tóxicos" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="nonToxic" name="No tóxicos" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment chart */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 flex items-center gap-2">
            <span className="w-2 h-6 bg-blue-500 rounded-full"></span>
            Análisis de Sentimientos
          </h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={60}
                  paddingAngle={5}
                  dataKey="percentage"
                  nameKey="sentiment"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {sentimentData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={getSentimentColor(entry.sentiment)} 
                    />
                  ))}
                </Pie>
                <Legend />
                <Tooltip 
                  formatter={(value) => [`${value}%`, "Porcentaje"]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Toxic comments section */}
      <div className="bg-white p-6 rounded-xl shadow-lg mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800">
            Comentarios Más Tóxicos
          </h2>
          <div className="flex items-center gap-4">
            <select
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>
          </div>
        </div>
        
        <div className="space-y-4">
          {topToxicComments.slice(0, topN).map((comment, index) => (
            <div 
              key={index} 
              className="p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
              style={{
                borderLeft: `4px solid ${getToxicityColor(comment.toxic_probability)}`,
                backgroundColor: `rgba(239, 68, 68, ${(comment.toxic_probability || 0) * 0.1})`
              }}
            >
              <div className="flex justify-between items-start">
                <p className="text-gray-800">{comment.text}</p>
                <span 
                  className="px-3 py-1 rounded-full text-sm font-medium"
                  style={{
                    backgroundColor: `rgba(239, 68, 68, ${(comment.toxic_probability || 0) * 0.3})`,
                    color: '#fff'
                  }}
                >
                  {Math.round((comment.toxic_probability || 0) * 100)}% tóxico
                </span>
              </div>
              <div className="flex justify-between mt-2 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                  </svg>
                  {comment.like_count_comment || 0} likes
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
                  {new Date(comment.published_at_comment || comment.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Statistics;