import React, { useState, useEffect, useMemo } from 'react';
import { 
  getSentimentAnalyzerAll,
  getSentimentAnalyzerByVideo,
  getVideoStatisticsAll,
  getVideoStatisticsById
} from '../services/services';
import { 
  Shield, 
  AlertTriangle, 
  MessageSquare, 
  Activity,
  Target,
  TrendingUp,
  Users,
  Eye,
  BarChart3
} from 'lucide-react';

// Importar componentes
import ToxicityDistribution from '../components/charts/global/ToxicityDistribution';
import VideoHeatmap from '../components/charts/global/VideoHeatmap';
import { GlobalMetricCards, SpecificMetricCards } from '../components/charts/global/MetricCards';

const Statistics = () => {
  // Extraer correctamente el videoId de la URL
  const urlPath = window.location.pathname;
  const pathParts = urlPath.split('/').filter(part => part !== '');
  const videoIdFromUrl = pathParts.length > 1 && pathParts[0] === 'statistics' && pathParts[1] !== '' ? pathParts[1] : null;
  
  // Estados principales
  const [allComments, setAllComments] = useState([]);
  const [allVideoStats, setAllVideoStats] = useState([]);
  const [specificVideoComments, setSpecificVideoComments] = useState([]);
  const [specificVideoStats, setSpecificVideoStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState(videoIdFromUrl ? 'specific' : 'global');
  const [selectedVideoId, setSelectedVideoId] = useState(videoIdFromUrl || '');

  // Cargar datos
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        if (activeView === 'global') {
          console.log('🔄 Cargando datos globales...');
          const [commentsResponse, statsResponse] = await Promise.all([
            getSentimentAnalyzerAll(),
            getVideoStatisticsAll()
          ]);
          
          setAllComments(commentsResponse.comments || []);
          setAllVideoStats(statsResponse.video_statistics || []);
          console.log('✅ Datos globales cargados');
          
        } else if (selectedVideoId) {
          console.log('🔄 Cargando datos para video:', selectedVideoId);
          const [commentsResponse, statsResponse] = await Promise.all([
            getSentimentAnalyzerByVideo(selectedVideoId),
            getVideoStatisticsById(selectedVideoId)
          ]);
          
          setSpecificVideoComments(commentsResponse.comments || []);
          setSpecificVideoStats(statsResponse.statistics || null);
          console.log('✅ Datos del video cargados');
        }
      } catch (err) {
        console.error('❌ Error cargando datos:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [activeView, selectedVideoId]);

  const handleVideoSelect = (videoId) => {
    setSelectedVideoId(videoId);
    setActiveView('specific');
    window.history.pushState({}, '', `/statistics/${videoId}`);
  };

  if (loading) return (
    <div className="h-full min-h-screen pt-24 bg-slate-50">
      <div className="container px-4 mx-auto">
        <div className="flex items-center justify-center py-20">
          <div className="text-lg text-slate-600">Loading statistics...</div>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="flex flex-col min-h-screen pt-24 mt-10 mb-10 bg-slate-50">
      <div className="container px-4 mx-auto">
        <div className="flex items-center justify-center py-20">
          <div className="px-4 py-3 text-red-700 bg-red-100 border border-red-400 rounded-lg">
            Error: {error}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full pt-24 mt-10 mb-10 bg-slate-50">
      <div className="container px-4 mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-4 text-3xl font-bold text-slate-800">
            Toxicity Analysis Dashboard
          </h1>
          
          {/* Vista Toggle */}
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => {
                setActiveView('global');
                setSelectedVideoId('');
                window.history.pushState({}, '', '/statistics');
              }}
              className={`px-6 py-2 rounded-full font-semibold text-lg transition-all duration-200 cursor-pointer ${
                activeView === 'global'
                  ? 'bg-red-500 text-white shadow-lg border-2 border-red-500'
                  : 'border-2 border-slate-300 text-slate-700 bg-slate-100/60 hover:bg-red-50/70 hover:text-red-600 hover:border-red-300/60'
              }`}
              style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
            >
              Global Analysis
            </button>
            
            {/* Selector de video directo */}
            <select
              value={selectedVideoId}
              onChange={(e) => handleVideoSelect(e.target.value)}
              className="px-4 py-3 bg-white border rounded-lg cursor-pointer border-slate-300 text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-500 min-w-80"
            >
              {!selectedVideoId && <option value="">Select video to analyze...</option>}
              
              {allVideoStats.map(videoItem => (
                <option key={videoItem.video_id} value={videoItem.video_id}>
                  Video {videoItem.video_id} ({videoItem.total_comments || 0} comments)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Vista Global */}
        {activeView === 'global' && (
          <>
            {/* Cards de métricas clave */}
            <GlobalMetricCards 
              allComments={allComments} 
              allVideoStats={allVideoStats} 
            />

            {/* Gráficos principales */}
            <div className="grid grid-cols-1 gap-8 mb-8 xl:grid-cols-2">
              {/* Gráfico de distribución de toxicidad */}
              <ToxicityDistribution allComments={allComments} />
              
              {/* Heatmap de videos */}
              <VideoHeatmap 
                allComments={allComments} 
                allVideoStats={allVideoStats}
                onVideoSelect={handleVideoSelect}
              />
            </div>
          </>
        )}

        {/* Vista específica */}
        {activeView === 'specific' && selectedVideoId && specificVideoComments.length > 0 && (
          <>
            {/* Cards específicos del video */}
            <SpecificMetricCards 
              specificVideoComments={specificVideoComments}
              specificVideoStats={specificVideoStats}
            />
            
          </>
        )}

        {/* Mensaje cuando no hay video seleccionado */}
        {activeView === 'specific' && !selectedVideoId && (
          <div className="py-20 text-center">
            <Target className="w-16 h-16 mx-auto mb-4 text-slate-400" />
            <h3 className="mb-2 text-xl font-semibold text-slate-600">
              Select a video to analyze
            </h3>
            <p className="text-slate-500">
              Choose a video from the dropdown menu to view its detailed toxicity analysis
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Statistics;