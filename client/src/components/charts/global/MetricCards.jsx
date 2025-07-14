import React, { useMemo } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  MessageSquare, 
  Eye,
  TrendingUp,
  Users
} from 'lucide-react';

// Componente para vista global
export const GlobalMetricCards = ({ allComments, allVideoStats }) => {
  // Definición de tipos de toxicidad
  const TOXICITY_TYPES = [
    'toxic', 'hatespeech', 'abusive', 'threat', 
    'provocative', 'obscene', 'racist', 'nationalist',
    'sexist', 'homophobic', 'religious_hate', 'radicalism'
  ];

  const TOXICITY_LABELS = {
    toxic: 'General Toxic',
    hatespeech: 'Hate Speech',
    abusive: 'Abusive',
    threat: 'Threat',
    provocative: 'Provocative',
    obscene: 'Obscene',
    racist: 'Racist',
    nationalist: 'Nationalist',
    sexist: 'Sexist',
    homophobic: 'Homophobic',
    religious_hate: 'Religious Hate',
    radicalism: 'Radicalism'
  };

  // Función helper para calcular toxicidad general
  const isToxicGeneral = (comment) => {
    return TOXICITY_TYPES.some(type => comment[`is_${type}`]);
  };

  // Cálculos
  const metrics = useMemo(() => {
    if (!allComments.length) return null;
    
    const totalComments = allComments.length;
    const totalVideos = allVideoStats.length;
    
    // Toxicidad general
    const toxicGeneralCount = allComments.filter(isToxicGeneral).length;
    const toxicGeneralRate = (toxicGeneralCount / totalComments * 100).toFixed(1);
    
    // Análisis detallado de toxicidad
    const toxicityBreakdown = {};
    TOXICITY_TYPES.forEach(type => {
      const count = allComments.filter(c => c[`is_${type}`]).length;
      toxicityBreakdown[type] = {
        count,
        percentage: (count / totalComments * 100).toFixed(1)
      };
    });
    
    // Tipo más frecuente
    const mostFrequentType = Object.entries(toxicityBreakdown)
      .sort(([,a], [,b]) => b.count - a.count)[0];
    
    // Videos por riesgo
    const videoRiskAnalysis = allVideoStats.map(videoItem => {
      const videoComments = allComments.filter(c => c.video_id === videoItem.video_id);
      const toxicCount = videoComments.filter(isToxicGeneral).length;
      const toxicRate = videoComments.length > 0 ? 
        (toxicCount / videoComments.length * 100) : 0;
      
      return { toxic_rate: parseFloat(toxicRate.toFixed(1)) };
    });
    
    const highRiskVideos = videoRiskAnalysis.filter(v => v.toxic_rate > 15).length;

    return {
      totalComments,
      totalVideos,
      toxicGeneralCount,
      toxicGeneralRate,
      mostFrequentType,
      highRiskVideos
    };
  }, [allComments, allVideoStats]);

  if (!metrics) return null;

  return (
    <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-4">
      <div className="p-6 bg-white border-l-4 border-blue-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Total Comments</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.totalComments.toLocaleString()}
            </p>
          </div>
          <MessageSquare className="w-8 h-8 text-blue-500" />
        </div>
      </div>

      <div className="p-6 bg-white border-l-4 border-red-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Toxicity Rate</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.toxicGeneralRate}%
            </p>
            <p className="text-sm text-slate-500">
              {metrics.toxicGeneralCount.toLocaleString()} comments
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
      </div>

      <div className="p-6 bg-white border-l-4 border-purple-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Most Common Type</h3>
            <p className="mt-2 text-xl font-bold text-slate-900">
              {TOXICITY_LABELS[metrics.mostFrequentType?.[0]] || 'N/A'}
            </p>
            <p className="text-sm text-slate-500">
              {metrics.mostFrequentType?.[1]?.percentage || 0}% of total
            </p>
          </div>
          <Shield className="w-8 h-8 text-purple-500" />
        </div>
      </div>

      <div className="p-6 bg-white border-l-4 border-orange-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Risk Videos</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.highRiskVideos}
            </p>
            <p className="text-sm text-slate-500">Toxicity &gt; 15%</p>
          </div>
          <Eye className="w-8 h-8 text-orange-500" />
        </div>
      </div>
    </div>
  );
};

// Componente para vista específica
export const SpecificMetricCards = ({ specificVideoComments, specificVideoStats }) => {
  // Definición de tipos de toxicidad
  const TOXICITY_TYPES = [
    'toxic', 'hatespeech', 'abusive', 'threat', 
    'provocative', 'obscene', 'racist', 'nationalist',
    'sexist', 'homophobic', 'religious_hate', 'radicalism'
  ];

  // Función helper para calcular toxicidad general
  const isToxicGeneral = (comment) => {
    return TOXICITY_TYPES.some(type => comment[`is_${type}`]);
  };

  const metrics = useMemo(() => {
    if (!specificVideoComments.length) return null;

    const totalComments = specificVideoComments.length;
    const toxicGeneralCount = specificVideoComments.filter(isToxicGeneral).length;
    
    // Detector de sarcasmo
    const potentialSarcasm = specificVideoComments.filter(c => 
      c.sentiment_type === 'positive' && isToxicGeneral(c)
    ).length;

    return {
      totalComments,
      toxicGeneralCount,
      toxicRate: ((toxicGeneralCount / totalComments) * 100).toFixed(1),
      potentialSarcasm,
      avgLikes: specificVideoStats?.mean_likes ? Math.round(specificVideoStats.mean_likes) : 0
    };
  }, [specificVideoComments, specificVideoStats]);

  if (!metrics) return null;

  return (
    <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-4">
      <div className="p-6 bg-white border-l-4 border-blue-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Total Comments</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.totalComments}
            </p>
          </div>
          <MessageSquare className="w-8 h-8 text-blue-500" />
        </div>
      </div>
      
      <div className="p-6 bg-white border-l-4 border-red-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Toxic Comments</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.toxicGeneralCount}
            </p>
            <p className="text-sm text-slate-500">
              {metrics.toxicRate}%
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
      </div>
      
      <div className="p-6 bg-white border-l-4 border-yellow-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Potential Sarcasm</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.potentialSarcasm}
            </p>
            <p className="text-sm text-slate-500">Positive + Toxic</p>
          </div>
          <TrendingUp className="w-8 h-8 text-yellow-500" />
        </div>
      </div>
      
      <div className="p-6 bg-white border-l-4 border-purple-500 shadow-lg rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-700">Average Engagement</h3>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {metrics.avgLikes}
            </p>
            <p className="text-sm text-slate-500">average likes</p>
          </div>
          <Users className="w-8 h-8 text-purple-500" />
        </div>
      </div>
    </div>
  );
};