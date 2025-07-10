import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';

import { 
  getVideoStatistics,
  getCommentsByVideo,
  formatToxicityDataForCharts,
  formatSentimentDataForCharts} 
from '../services/services';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import {
  MessageCircle, AlertTriangle, Heart, Shield, Activity
} from 'lucide-react';

const Statistics = () => {
  const { videoId } = useParams();
  const [stats, setStats] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reportRef = useRef();

  useEffect(() => {
  const fetchData = async () => {
    console.log("Componente montado, videoId:", videoId);
    if (!videoId) {
      setError("No se proporcionó un ID de video en la URL.");
      setLoading(false);
      return;
    }
    try {
      const [statsData, commentsData] = await Promise.all([
        getVideoStatistics(videoId),
        getCommentsByVideo(videoId)
      ]);
      console.log("Datos recibidos:", { statsData, commentsData });

      if (!statsData) {
        throw new Error("No se recibieron estadísticas del video.");
      }
      if (!commentsData) {
        throw new Error("No se recibieron comentarios del video.");
      }

      setStats(statsData);
      setComments(commentsData);
    } catch (err) {
      console.error("Error al cargar datos:", err);
      setError(err.message || "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, [videoId]);
  // Renderizado condicional mejorado
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p>Cargando estadísticas para el video {videoId}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
        <h3 className="font-bold mb-2">Error</h3>
        <p>{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-3 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!stats || !comments.length) {
    return (
      <div className="text-center py-20">
        <p>No se encontraron datos para el video {videoId}</p>
        <p className="text-sm text-gray-500 mt-2">
          Verifica que el ID del video sea correcto
        </p>
      </div>
    );
  }

  // Preparación de datos para gráficos
  const toxicityData = formatToxicityDataForCharts(stats.toxicity_stats);
  const sentimentData = formatSentimentDataForCharts(stats.sentiment_distribution);
  const toxicityOverTime = comments
    .filter(c => c.published_at)
    .sort((a, b) => new Date(a.published_at) - new Date(b.published_at))
    .map(comment => ({
      date: new Date(comment.published_at).toLocaleDateString(),
      toxicity: Math.round((comment.toxic_probability || 0) * 100)
    }));

  return (
    <div ref={reportRef} className="container mx-auto px-4 py-8">
      {/* Contenido principal */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">
          Estadísticas del Video: {videoId}
        </h1>
        
        {/* Sección de métricas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <MetricCard 
            icon={<MessageCircle size={24} className="text-blue-500" />}
            title="Comentarios"
            value={stats.total_comments}
          />
          <MetricCard 
            icon={<AlertTriangle size={24} className="text-red-500" />}
            title="Toxicidad"
            value={`${Math.round((stats.toxicity_stats?.average_toxicity || 0) * 100)}%`}
          />
          <MetricCard 
            icon={<Heart size={24} className="text-pink-500" />}
            title="Likes promedio"
            value={
              comments.length > 0
                ? (comments.reduce((acc, c) => acc + (c.like_count || 0), 0) / comments.length).toFixed(1)
                : '0.0'
            }
/>
          <MetricCard 
            icon={<Shield size={24} className="text-purple-500" />}
            title="Sentimiento"
            value={stats.sentiment_distribution?.dominant_sentiment?.toUpperCase() || 'NEUTRAL'}
          />
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <ChartContainer title="Distribución de Toxicidad">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toxicityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="toxic" fill="#ef4444" name="Tóxicos" />
                <Bar dataKey="nonToxic" fill="#3b82f6" name="No tóxicos" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>

          <ChartContainer title="Distribución de Sentimientos">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={
                      entry.name === 'positive' ? '#10B981' :
                      entry.name === 'negative' ? '#EF4444' : '#3B82F6'
                    } />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Toxicidad en el tiempo */}
        <ChartContainer title="Toxicidad a lo largo del tiempo">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={toxicityOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="toxicity" 
                stroke="#ef4444" 
                name="Toxicidad (%)"
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>
    </div>
  );
};

// Componentes auxiliares
const MetricCard = ({ icon, title, value }) => (
  <div className="bg-white border rounded-lg p-4 shadow-sm">
    <div className="flex items-center gap-3 mb-2">
      {icon}
      <h3 className="font-medium text-gray-700">{title}</h3>
    </div>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const ChartContainer = ({ title, children }) => (
  <div className="bg-white border rounded-lg p-4 shadow-sm">
    <h2 className="text-lg font-semibold mb-4">{title}</h2>
    {children}
  </div>
);

export default Statistics;