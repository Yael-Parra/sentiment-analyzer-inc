import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from '../pages/Home.jsx';
import LinkAnalysis from '../pages/LinkAnalysis.jsx';
import Statistics from '../pages/Statistics.jsx';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/link-analysis" element={<LinkAnalysis />} />
      <Route path="/statistics" element={<Statistics />} /> 
      <Route path="/statistics/:videoId" element={<Statistics />} />
      <Route path="*" element={<div>Not Found</div>} />
    </Routes>
  );
}

export default AppRoutes;