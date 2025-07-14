import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, AlertTriangle, ThumbsUp, MessageSquare } from 'lucide-react';

const CommentsList = ({ specificVideoComments }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const commentsPerPage = 10;

  // Definición de tipos de toxicidad
  const TOXICITY_TYPES = [
    'toxic', 'hatespeech', 'abusive', 'threat', 
    'provocative', 'obscene', 'racist', 'nationalist',
    'sexist', 'homophobic', 'religious_hate', 'radicalism'
  ];

  const TOXICITY_LABELS = {
    toxic: 'Toxic',
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

  const TOXICITY_COLORS = {
    toxic: 'bg-red-100 text-red-800 border-red-200',
    hatespeech: 'bg-red-100 text-red-900 border-red-300',
    abusive: 'bg-orange-100 text-orange-800 border-orange-200',
    threat: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    provocative: 'bg-amber-100 text-amber-800 border-amber-200',
    obscene: 'bg-pink-100 text-pink-800 border-pink-200',
    racist: 'bg-purple-100 text-purple-800 border-purple-200',
    nationalist: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    sexist: 'bg-violet-100 text-violet-800 border-violet-200',
    homophobic: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200',
    religious_hate: 'bg-rose-100 text-rose-800 border-rose-200',
    radicalism: 'bg-red-200 text-red-900 border-red-300'
  };

  const SENTIMENT_COLORS = {
    positive: 'bg-green-100 text-green-800',
    negative: 'bg-red-100 text-red-800',
    neutral: 'bg-gray-100 text-gray-800'
  };

  // Función helper para obtener las etiquetas de toxicidad de un comentario
  const getToxicityLabels = (comment) => {
    return TOXICITY_TYPES.filter(type => comment[`is_${type}`]);
  };

  // Cálculos de paginación
  const paginatedComments = useMemo(() => {
    const indexOfLastComment = currentPage * commentsPerPage;
    const indexOfFirstComment = indexOfLastComment - commentsPerPage;
    return specificVideoComments.slice(indexOfFirstComment, indexOfLastComment);
  }, [specificVideoComments, currentPage]);

  const totalPages = Math.ceil(specificVideoComments.length / commentsPerPage);

  // Funciones de navegación
  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const goToPage = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  // Generar números de página para mostrar
  const getPageNumbers = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];
    let l;

    for (let i = 1; i <= totalPages; i++) {
      if (i == 1 || i == totalPages || i >= currentPage - delta && i <= currentPage + delta) {
        range.push(i);
      }
    }

    range.forEach((i) => {
      if (l) {
        if (i - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (i - l !== 1) {
          rangeWithDots.push('...');
        }
      }
      rangeWithDots.push(i);
      l = i;
    });

    return rangeWithDots;
  };

  return (
    <div className="p-6 mb-8 bg-white shadow-lg rounded-xl">
      <h2 className="mb-6 text-xl font-semibold text-slate-800">
        Comments Analysis
      </h2>

      {/* Lista de comentarios */}
      <div className="mb-6 space-y-4">
        {paginatedComments.map((comment, index) => {
          const toxicityLabels = getToxicityLabels(comment);
          const hasToxicity = toxicityLabels.length > 0;
          
          return (
            <div 
              key={comment.comment_id || index} 
              className={`p-4 border rounded-lg transition-colors ${
                hasToxicity ? 'border-red-200 bg-red-50/30' : 'border-green-200 bg-green-50/20'
              } hover:shadow-md`}
            >
              {/* Contenido del comentario */}
              <p className="mb-3 leading-relaxed text-slate-700">
                {comment.text || comment.comment_text || 'No text available'}
              </p>

              {/* Metadatos y etiquetas */}
              <div className="flex flex-wrap items-center gap-2">
                {/* TOXICITY ANALYSIS */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Toxicity:</span>
                  
                  {/* Si tiene etiquetas de toxicidad */}
                  {toxicityLabels.length > 0 ? (
                    toxicityLabels.map(type => (
                      <span 
                        key={type}
                        className={`px-2 py-1 text-xs font-medium rounded-full border ${TOXICITY_COLORS[type]}`}
                      >
                        <AlertTriangle className="inline w-3 h-3 mr-1" />
                        {TOXICITY_LABELS[type]}
                      </span>
                    ))
                  ) : (
                    /* Si NO tiene toxicidad - mostrar etiqueta Clean */
                    <span className="px-2 py-1 text-xs font-medium text-green-800 bg-green-100 border border-green-200 rounded-full">
                      ✓ Clean
                    </span>
                  )}
                </div>

                {/* Separador principal */}
                <div className="w-px h-4 mx-2 bg-slate-400" />

                {/* SENTIMENT ANALYSIS */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Sentiment:</span>
                  {comment.sentiment_type && (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${SENTIMENT_COLORS[comment.sentiment_type]}`}>
                      {comment.sentiment_type.charAt(0).toUpperCase() + comment.sentiment_type.slice(1)}
                    </span>
                  )}
                  {comment.sentiment_intensity && (
                    <span className="px-2 py-1 text-xs font-medium border rounded-full bg-slate-100 text-slate-700 border-slate-200">
                      Intensity: {comment.sentiment_intensity}
                    </span>
                  )}
                </div>

                {/* Separador */}
                <div className="w-px h-4 mx-2 bg-slate-300" />

                {/* ENGAGEMENT METRICS */}
                <div className="flex items-center gap-3">
                  {/* Likes */}
                  {comment.total_likes_comment !== undefined && (
                    <span className="flex items-center text-xs text-slate-600">
                      <ThumbsUp className="w-3 h-3 mr-1" />
                      {comment.total_likes_comment}
                    </span>
                  )}

                  {/* Replies */}
                  {comment.reply_count !== undefined && (
                    <span className="flex items-center text-xs text-slate-600">
                      <MessageSquare className="w-3 h-3 mr-1" />
                      {comment.reply_count}
                    </span>
                  )}
                </div>

                {/* Autor si está disponible */}
                {comment.author_name && (
                  <span className="ml-auto text-xs text-slate-500">
                    by {comment.author_name}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="text-sm text-slate-600">
          Showing {((currentPage - 1) * commentsPerPage) + 1} to {Math.min(currentPage * commentsPerPage, specificVideoComments.length)} of {specificVideoComments.length} comments
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={prevPage}
            disabled={currentPage === 1}
            className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {getPageNumbers().map((number, index) => (
            number === '...' ? (
              <span key={index} className="px-3 py-1">...</span>
            ) : (
              <button
                key={index}
                onClick={() => goToPage(number)}
                className={`px-3 py-1 rounded-lg font-medium text-sm transition-colors ${
                  currentPage === number
                    ? 'bg-red-500 text-white'
                    : 'hover:bg-slate-100 text-slate-700'
                }`}
              >
                {number}
              </button>
            )
          ))}

          <button
            onClick={nextPage}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default CommentsList;