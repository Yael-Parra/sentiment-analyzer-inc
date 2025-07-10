// ⛳ Statistics.jsx
import React, { useState, useEffect, useRef } from 'react';
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
import { useParams } from 'react-router-dom';
import html2pdf from 'html2pdf.js';

const Statistics = () => {
  const { videoId } = useParams();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [topN, setTopN] = useState(5);
  const reportRef = useRef();

  const COLORS = ['#00B894', '#FF7675', '#74B9FF', '#E17055'];

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getVideoStatistics(videoId);
        setStats(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [videoId]);

  if (loading) return <div className="text-center py-20">Cargando estadísticas...</div>;
  if (error) return <div className="text-red-500 text-center py-20">Error: {error}</div>;
  if (!stats) return <div className="text-center py-20">No hay datos disponibles</div>;

  // Formateos de datos
  const toxicityData = formatToxicityDataForCharts(stats.toxicity_distribution);
  const sentimentData = formatSentimentDataForCharts(stats.sentiment_analysis);
  const engagementMetrics = calculateEngagementMetrics(stats.comments, stats.engagement_stats);
  const topToxicComments = getTopToxicComments(stats.comments);

  const pieEngagementData = [
    { name: 'Con URLs', value: engagementMetrics.commentsWithUrls, color: '#6C5CE7' },
    { name: 'Con Menciones', value: engagementMetrics.commentsWithTags, color: '#FDCB6E' },
  ];

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

  const toxicityOverTime = stats.comments
    .map(comment => ({
      time: new Date(comment.published_at_comment).toLocaleDateString(),
      toxicity: Math.round(comment.toxic_probability * 100)
    }))
    .sort((a, b) => new Date(a.time) - new Date(b.time));

  return (
    <div ref={reportRef} className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">Estadísticas del Video</h1>

      <div className="flex justify-end mb-4">
        <button
          onClick={handleDownloadPDF}
          className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700"
        >
          Descargar PDF
        </button>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Comentarios Analizados</h3>
          <p className="text-4xl font-bold text-blue-600">{stats.total_comments}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Toxicidad Promedio</h3>
          <p className="text-4xl font-bold text-red-600">
            {stats.toxicity_distribution.average_toxicity.toFixed(2)}%
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Sentimiento Dominante</h3>
          <p className="text-4xl font-bold text-green-600">
            {stats.sentiment_analysis.dominant_sentiment.toUpperCase()}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Máx. Likes en Comentario</h3>
          <p className="text-4xl font-bold text-purple-600">{engagementMetrics.maxLikes}</p>
        </div>
      </div>

      {/* Gráfico de línea - Toxicidad vs Tiempo */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-semibold mb-4">Toxicidad a lo Largo del Tiempo</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={toxicityOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="toxicity" stroke="#E17055" name="Toxicidad (%)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Distribución de Toxicidad */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-semibold mb-4">Distribución de Toxicidad</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={toxicityData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" name="Tóxicos" fill="#FF6B6B" />
              <Bar dataKey="negative" name="No tóxicos" fill="#74B9FF" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Distribución de Sentimientos */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-semibold mb-4">Distribución de Sentimientos</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                labelLine={false}
                dataKey="count"
                nameKey="sentiment"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`sent-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Engagement por Tipo */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-semibold mb-4">Engagement por Tipo de Comentario</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieEngagementData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                dataKey="value"
              >
                {pieEngagementData.map((entry, index) => (
                  <Cell key={`eng-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comentarios Tóxicos */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Comentarios Más Tóxicos</h2>
          <select
            value={topN}
            onChange={(e) => setTopN(parseInt(e.target.value))}
            className="border border-gray-300 rounded px-2 py-1"
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
          </select>
        </div>
        <div className="space-y-4">
          {topToxicComments.slice(0, topN).map((comment, index) => (
            <div key={index} className="border-l-4 border-red-500 pl-4 py-2 bg-red-50">
              <div className="flex justify-between items-start">
                <p className="font-medium">{comment.text}</p>
                <span className="bg-red-500 text-white px-2 py-1 rounded text-sm">
                  {Math.round(comment.toxic_probability * 100)}% tóxico
                </span>
              </div>
              <div className="flex justify-between text-sm text-gray-600 mt-1">
                <span>👍 {comment.like_count} likes</span>
                <span>{new Date(comment.published_at_comment).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Statistics;
