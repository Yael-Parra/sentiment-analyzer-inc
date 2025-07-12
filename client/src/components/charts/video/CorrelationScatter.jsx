import React, { useMemo } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const CorrelationScatter = ({ specificVideoComments }) => {
  // Colores
  const COLORS = {
    toxic: '#dc2626',
    success: '#10b981'
  };

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

  // Cálculos
  const scatterData = useMemo(() => {
    if (!specificVideoComments.length) return [];

    // Análisis de correlación sentiment vs toxicity
    return specificVideoComments.map((c, index) => ({
      x: c.sentiment_score || 0,
      y: Math.max(...TOXICITY_TYPES.map(type => c[`${type}_probability`] || 0)),
      size: Math.max(c.total_likes_comment || 0, 1),
      isToxic: isToxicGeneral(c),
      sentiment_type: c.sentiment_type || 'neutral',
      id: index
    }));
  }, [specificVideoComments]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Sentiment - Toxicity Correlation
      </h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart data={scatterData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="x" 
              name="Sentiment Score"
              domain={[-1, 1]}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              name="Toxicity Score"
              domain={[0, 1]}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name) => [
                typeof value === 'number' ? value.toFixed(2) : value, 
                name === 'x' ? 'Sentiment Score' : 
                name === 'y' ? 'Toxicity Score' : 
                name === 'size' ? 'Likes' : name
              ]}
              labelFormatter={() => 'Comment'}
            />
            <Scatter 
              name="Comments" 
              dataKey="y" 
              fill={(entry) => entry.isToxic ? COLORS.toxic : COLORS.success}
              fillOpacity={0.6}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-slate-600">
        <p><strong>Interpretation:</strong> Points in the upper right quadrant (positive + toxic) may indicate sarcasm.</p>
      </div>
    </div>
  );
};

export default CorrelationScatter;