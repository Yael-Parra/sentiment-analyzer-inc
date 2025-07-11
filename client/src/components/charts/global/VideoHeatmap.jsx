import React, { useMemo } from 'react';

const VideoHeatmap = ({ allComments, allVideoStats, onVideoSelect }) => {
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

  // Cálculo de datos del heatmap
  const heatmapData = useMemo(() => {
    if (!allComments.length || !allVideoStats.length) return [];

    // Videos por riesgo
    const videoRiskAnalysis = allVideoStats.map(videoItem => {
      const videoComments = allComments.filter(c => c.video_id === videoItem.video_id);
      const toxicCount = videoComments.filter(isToxicGeneral).length;
      const toxicRate = videoComments.length > 0 ? 
        (toxicCount / videoComments.length * 100) : 0;
      
      return {
        video_id: videoItem.video_id,
        total_comments: videoComments.length,
        toxic_count: toxicCount,
        toxic_rate: parseFloat(toxicRate.toFixed(1))
      };
    });

    // Ordenar por tasa de toxicidad y retornar top 10
    return videoRiskAnalysis.sort((a, b) => b.toxic_rate - a.toxic_rate).slice(0, 10);
  }, [allComments, allVideoStats]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Most Problematic Videos
      </h2>
      <div className="overflow-y-auto h-80">
        <div className="space-y-3">
          {heatmapData.map((videoItem, index) => (
            <div 
              key={videoItem.video_id} 
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50"
            >
              <div className="flex-1">
                <div className="font-mono text-sm text-slate-600">
                  Video {videoItem.video_id}
                </div>
                <div className="text-xs text-slate-500">
                  {videoItem.total_comments} comments • {videoItem.toxic_count} toxic
                </div>
                <div className="w-full h-2 mt-2 bg-gray-200 rounded-full">
                  <div 
                    className={`h-2 rounded-full ${
                      videoItem.toxic_rate > 20 ? 'bg-red-500' :
                      videoItem.toxic_rate > 10 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(videoItem.toxic_rate, 100)}%` }}
                  ></div>
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  videoItem.toxic_rate > 20 ? 'bg-red-100 text-red-800' :
                  videoItem.toxic_rate > 10 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {videoItem.toxic_rate}%
                </span>
                <button
                  onClick={() => onVideoSelect(videoItem.video_id)}
                  className="px-3 py-1 text-sm text-red-500 rounded hover:text-red-700 hover:bg-red-50"
                >
                  Statistics
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VideoHeatmap;