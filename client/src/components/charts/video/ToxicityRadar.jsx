import React, { useMemo } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip
} from 'recharts';

const ToxicityRadar = ({ specificVideoComments }) => {
  // Constantes
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

  const COLORS = {
    toxic: '#dc2626'
  };

  // Cálculos
  const radarData = useMemo(() => {
    if (!specificVideoComments.length) return [];

    const totalComments = specificVideoComments.length;
    
    // Breakdown detallado de toxicidad
    const toxicityBreakdown = {};
    TOXICITY_TYPES.forEach(type => {
      const count = specificVideoComments.filter(c => c[`is_${type}`]).length;
      toxicityBreakdown[type] = {
        count,
        percentage: (count / totalComments * 100).toFixed(1)
      };
    });
    
    // Datos para el radar
    return TOXICITY_TYPES.map(type => ({
      type: TOXICITY_LABELS[type],
      value: parseFloat(toxicityBreakdown[type].percentage),
      count: toxicityBreakdown[type].count,
      fullMark: 100
    }));
  }, [specificVideoComments]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Video Toxicity Profile
      </h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis 
              dataKey="type" 
              fontSize={10}
              tick={{ fontSize: 10 }}
            />
            <PolarRadiusAxis 
              angle={90} 
              domain={[0, 'dataMax']}
              fontSize={8}
            />
            <Radar
              name="Percentage"
              dataKey="value"
              stroke={COLORS.toxic}
              fill={COLORS.toxic}
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Tooltip 
              formatter={(value, name, props) => [
                `${value}% (${props.payload.count} comments)`, 
                "Toxicity"
              ]}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ToxicityRadar;