import React, { useMemo } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts';

const SarcasmDetector = ({ specificVideoComments }) => {
  // Colores
  const COLORS = {
    warning: '#f59e0b',
    neutral: '#6b7280'
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
  const sarcasmData = useMemo(() => {
    if (!specificVideoComments.length) return [];

    const totalComments = specificVideoComments.length;
    
    // Detector de sarcasmo
    const potentialSarcasm = specificVideoComments.filter(c => 
      c.sentiment_type === 'positive' && isToxicGeneral(c)
    ).length;
    
    return [
      { name: 'Normal Comments', value: totalComments - potentialSarcasm },
      { name: 'Potential Sarcasm', value: potentialSarcasm }
    ];
  }, [specificVideoComments]);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Sarcasm Detector
      </h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={sarcasmData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={40}
              paddingAngle={5}
              dataKey="value"
              label={({ name, value }) => `${name}: ${value}`}
            >
              {sarcasmData?.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.name === 'Potential Sarcasm' ? COLORS.warning : COLORS.neutral} 
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-slate-600">
        <p><strong>Criteria:</strong> Comments classified as positive but detected as toxic.</p>
      </div>
    </div>
  );
};

export default SarcasmDetector;