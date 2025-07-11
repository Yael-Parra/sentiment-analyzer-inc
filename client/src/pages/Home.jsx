import React from 'react';

const Home = () => {
  return (
    <div className="mt-40 mb-40 flex justify-center px-4">
      <div className="bg-white shadow-xl rounded-2xl p-8 max-w-3xl w-full text-center">
        <h1 className="text-3xl md:text-4xl font-bold text-red-500 mb-6">
          YouTube Sentiment & Toxicity Analyzer
        </h1>

        <p className="text-gray-700 text-lg mb-6">
          This application analyzes comments from YouTube videos to detect:
        </p>

        <ul className="text-left list-disc list-inside text-gray-800 text-base mb-6 leading-relaxed">
          <li><strong>Overall sentiment</strong> (positive, negative, neutral)</li>
          <li><strong>Toxicity</strong> across 12 categories such as hate, racism, sexism, threats, and more</li>
          <li><strong>Engagement statistics</strong> including likes, mentions, and URLs</li>
        </ul>

        <p className="text-gray-700 text-base mb-8">
          Just enter the video URL or ID to get insights processed by AI-powered models. <br />
          Perfect for content creators, researchers, and brands seeking to better understand audience interaction.
        </p>

        <a
          href="/link-analysis"
          className="inline-block bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
        >
          Start Analysis
        </a>
      </div>
    </div>
  );
};

export default Home;