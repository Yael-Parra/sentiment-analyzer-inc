import React, { useMemo } from 'react';

const RiskAssessment = ({ specificVideoComments }) => {
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

  // Función helper para calcular toxicidad general
  const isToxicGeneral = (comment) => {
    return TOXICITY_TYPES.some(type => comment[`is_${type}`]);
  };

  // Cálculos
  const riskAnalysis = useMemo(() => {
    if (!specificVideoComments.length) return null;

    const totalComments = specificVideoComments.length;
    const toxicGeneralCount = specificVideoComments.filter(isToxicGeneral).length;
    const toxicRate = (toxicGeneralCount / totalComments * 100);
    
    // Análisis detallado de toxicidad
    const toxicityBreakdown = {};
    TOXICITY_TYPES.forEach(type => {
      const count = specificVideoComments.filter(c => c[`is_${type}`]).length;
      toxicityBreakdown[type] = {
        count,
        percentage: (count / totalComments * 100).toFixed(1)
      };
    });
    
    // Tipo más problemático
    const mostProblematicType = Object.entries(toxicityBreakdown)
      .filter(([, data]) => data.count > 0)
      .sort(([,a], [,b]) => b.count - a.count)[0];
    
    // Detector de sarcasmo
    const potentialSarcasm = specificVideoComments.filter(c => 
      c.sentiment_type === 'positive' && isToxicGeneral(c)
    ).length;
    
    // Determinar nivel de riesgo
    const riskLevel = toxicRate > 20 ? 'High' : toxicRate > 10 ? 'Medium' : toxicRate > 5 ? 'Low' : 'Minimal';
    const riskColor = toxicRate > 20 ? 'red' : toxicRate > 10 ? 'yellow' : toxicRate > 5 ? 'orange' : 'green';
    
    return {
      toxicRate: toxicRate.toFixed(1),
      riskLevel,
      riskColor,
      mostProblematicType,
      potentialSarcasm
    };
  }, [specificVideoComments]);

  if (!riskAnalysis) return null;

  return (
    <div className="p-6 mb-8 bg-white shadow-lg rounded-xl">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">
        Video Risk Assessment
      </h2>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className={`p-4 rounded-lg border-l-4 ${
          riskAnalysis.riskColor === 'red' ? 'border-red-500 bg-red-50' :
          riskAnalysis.riskColor === 'yellow' ? 'border-yellow-500 bg-yellow-50' :
          riskAnalysis.riskColor === 'orange' ? 'border-orange-500 bg-orange-50' :
          'border-green-500 bg-green-50'
        }`}>
          <h3 className="font-semibold text-slate-700">Risk Level</h3>
          <p className={`text-2xl font-bold ${
            riskAnalysis.riskColor === 'red' ? 'text-red-700' :
            riskAnalysis.riskColor === 'yellow' ? 'text-yellow-700' :
            riskAnalysis.riskColor === 'orange' ? 'text-orange-700' :
            'text-green-700'
          }`}>
            {riskAnalysis.riskLevel}
          </p>
          <p className="text-sm text-slate-600">
            {riskAnalysis.toxicRate}% toxic comments
          </p>
        </div>
        
        <div className="p-4 border-l-4 border-blue-500 rounded-lg bg-blue-50">
          <h3 className="font-semibold text-slate-700">Most Problematic Type</h3>
          <p className="text-xl font-bold text-blue-700">
            {riskAnalysis.mostProblematicType ? 
              TOXICITY_LABELS[riskAnalysis.mostProblematicType[0]] : 'None'}
          </p>
          <p className="text-sm text-blue-600">
            {riskAnalysis.mostProblematicType ? 
              `${riskAnalysis.mostProblematicType[1].count} comments` : 'N/A'}
          </p>
        </div>
        
        <div className="p-4 border-l-4 border-purple-500 rounded-lg bg-purple-50">
          <h3 className="font-semibold text-slate-700">Recommendation</h3>
          <p className="text-sm text-purple-700">
            {parseFloat(riskAnalysis.toxicRate) > 20 ? 'Urgent moderation required' :
             parseFloat(riskAnalysis.toxicRate) > 10 ? 'Review highlighted comments' :
             parseFloat(riskAnalysis.toxicRate) > 5 ? 'Regular monitoring recommended' :
             'Healthy community'}
          </p>
          {riskAnalysis.potentialSarcasm > 0 && (
            <p className="mt-2 text-xs text-purple-600">
              ⚠️ Potential sarcasm detected: manual review advised
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskAssessment;