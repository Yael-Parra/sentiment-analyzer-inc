import React, { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { BarChart3 } from 'lucide-react';

const ToxicityDistribution = ({ allComments }) => {
  // Colores y configuración
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

  // Cálculos
  const toxicityChartData = useMemo(() => {
    if (!allComments || allComments.length === 0) return [];
    
    const totalComments = allComments.length;
    
    // Análisis detallado de toxicidad
    const toxicityBreakdown = {};
    TOXICITY_TYPES.forEach(type => {
      const count = allComments.filter(c => c[`is_${type}`]).length;
      toxicityBreakdown[type] = {
        count,
        percentage: (count / totalComments * 100).toFixed(1)
      };
    });
    
    // Datos para gráfico de barras
    const chartData = TOXICITY_TYPES.map((type) => ({
      name: TOXICITY_LABELS[type],
      value: parseFloat(toxicityBreakdown[type]?.percentage || 0),
      count: toxicityBreakdown[type]?.count || 0
    }))
    .filter(item => item.value > 0) // Solo mostrar tipos que tienen datos
    .sort((a, b) => b.value - a.value); // Ordenar de mayor a menor porcentaje
    
    // Si no hay datos, crear datos de ejemplo para mostrar la estructura
    return chartData.length > 0 ? chartData : 
      TOXICITY_TYPES.slice(0, 3).map((type) => ({
        name: TOXICITY_LABELS[type],
        value: 0,
        count: 0
      }));
  }, [allComments]);

  const hasData = toxicityChartData.some(item => item.value > 0);

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl xl:col-span-2">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Distribution of Toxicity Types
      </h2>
      
      {hasData ? (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={toxicityChartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={11}
              />
              <YAxis 
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip 
                formatter={(value, name) => [`${value}%`, 'Percentage']}
                labelFormatter={(label, payload) => {
                  if (payload && payload[0]) {
                    const data = payload[0].payload;
                    return `${label} - ${data.count} comments`;
                  }
                  return label;
                }}
                contentStyle={{ 
                  backgroundColor: '#f8fafc', 
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px'
                }}
              />
              <Bar 
                dataKey="value" 
                radius={[4, 4, 0, 0]}
                name="Toxicity Percentage"
                fill="#ef4444"
                fillOpacity={0.8}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="flex items-center justify-center h-96 text-slate-500">
          <div className="text-center">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-slate-300" />
            <div>
              <p className="text-lg font-medium">No toxicity detected</p>
              <p className="mt-1 text-sm">All comments appear to be clean</p>
              <div className="p-3 mt-4 rounded-lg bg-green-50">
                <p className="text-sm text-green-700">
                  ✅ {allComments?.length || 0} comments analyzed
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ToxicityDistribution;