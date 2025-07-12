import React, { useMemo } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts';

const SentimentPie = ({ specificVideoComments }) => {
  // Colores
  const COLORS = {
    positive: '#10b981',
    negative: '#ef4444',
    neutral: '#6b7280'
  };

  // Cálculos
  const sentimentChartData = useMemo(() => {
    if (!specificVideoComments.length) return [];

    const totalComments = specificVideoComments.length;
    
    // Distribución de sentimientos
    const sentimentDistribution = specificVideoComments.reduce((acc, c) => {
      const sentiment = c.sentiment_type || 'neutral';
      acc[sentiment] = (acc[sentiment] || 0) + 1;
      return acc;
    }, {});
    
    // Datos para el gráfico
    return Object.entries(sentimentDistribution).map(([sentiment, count]) => ({
      sentiment: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
      count,
      percentage: ((count / totalComments) * 100).toFixed(1)
    }));
  }, [specificVideoComments]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Emotional Context
      </h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={sentimentChartData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={40}
              paddingAngle={5}
              dataKey="count"
              label={({ sentiment, percentage }) => `${sentiment}: ${percentage}%`}
            >
              {sentimentChartData?.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.sentiment === 'Positive' ? COLORS.positive : 
                        entry.sentiment === 'Negative' ? COLORS.negative : COLORS.neutral} 
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SentimentPie;