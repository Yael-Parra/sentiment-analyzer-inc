import React, { useMemo } from 'react';
import {
  ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const EngagementComparison = ({ allComments }) => {
  // Colores
  const COLORS = {
    success: '#10b981',
    blue: '#3b82f6'
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
  const engagementData = useMemo(() => {
    if (!allComments.length) return [];

    // Correlación engagement vs toxicidad
    const engagementAnalysis = allComments.reduce((acc, comment) => {
      const isToxic = isToxicGeneral(comment);
      const category = isToxic ? 'toxic' : 'clean';
      
      if (!acc[category]) {
        acc[category] = { totalLikes: 0, count: 0 };
      }
      
      acc[category].totalLikes += (comment.total_likes_comment || 0);
      acc[category].count += 1;
      
      return acc;
    }, {});

    // Datos para el gráfico
    return Object.entries(engagementAnalysis).map(([category, data]) => ({
      category: category === 'toxic' ? 'Toxic Comments' : 'Clean Comments',
      avgLikes: data.count > 0 ? parseFloat((data.totalLikes / data.count).toFixed(1)) : 0,
      totalComments: data.count
    }));
  }, [allComments]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Engagement vs Toxicity
      </h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={engagementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="avgLikes" fill={COLORS.success} name="Average Likes" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EngagementComparison;