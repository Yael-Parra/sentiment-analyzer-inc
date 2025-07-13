import React from 'react';
import { 
  Play, 
  MessageCircle, 
  BarChart3, 
  Shield, 
  Heart, 
  TrendingUp, 
  Zap, 
  CheckCircle,
  ArrowRight,
  Users,
  Eye
} from 'lucide-react';

const Home = () => {
  const features = [
    {
      icon: <MessageCircle className="text-blue-500" size={28} />,
      title: "Sentiment Analysis",
      description: "Detect positive, negative, and neutral emotions in real-time"
    },
    {
      icon: <Shield className="text-red-500" size={28} />,
      title: "Toxicity Detection",
      description: "Identify 12 types of toxic content: hate, racism, threats and more"
    },
    {
      icon: <BarChart3 className="text-green-500" size={28} />,
      title: "Engagement Metrics",
      description: "Analyze likes, mentions, URLs and interaction patterns"
    },
    {
      icon: <Zap className="text-yellow-500" size={28} />,
      title: "AI Processing",
      description: "Powered by state-of-the-art machine learning models"
    }
  ];

  const stats = [
    { number: "12+", label: "Toxicity Types", icon: <Shield size={20} /> },
    { number: "99%", label: "Accuracy", icon: <CheckCircle size={20} /> },
    { number: "500+", label: "Comments/min", icon: <Zap size={20} /> },
    { number: "3", label: "Sentiment Types", icon: <Heart size={20} /> }
  ];

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F7FAFC' }}>
      {/* Hero Section */}
      <div className="pt-20 pb-16 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Main Content */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-red-100 text-red-600 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Zap size={16} />
              Intelligent YouTube Comment Analysis
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-6 leading-tight">
              <span className="text-red-500">YouTube</span> Sentiment & <br />
              <span className="text-gray-800">
                Toxicity Analyzer
              </span>
            </h1>

            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Discover what your audiences really think. Analyze sentiment, detect toxicity 
              and get deep insights from any YouTube video with AI technology.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <a
                href="/link-analysis"
                className="group bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-8 rounded-xl shadow-lg transition-all duration-300 transform hover:scale-105 hover:shadow-xl flex items-center gap-2"
              >
                <Play size={20} />
                Start Analysis
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </a>
              
              <button className="text-gray-600 hover:text-red-500 font-medium py-4 px-6 rounded-xl border border-gray-200 hover:border-red-200 transition-all duration-300 flex items-center gap-2">
                <Eye size={20} />
                Watch Demo
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
            {stats.map((stat, index) => (
              <div key={index} className="bg-white/70 backdrop-blur-sm rounded-2xl p-6 text-center border border-white/20 hover:bg-white/90 transition-all duration-300">
                <div className="flex justify-center mb-2 text-red-500">
                  {stat.icon}
                </div>
                <div className="text-3xl font-bold text-gray-800 mb-1">{stat.number}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 px-4 bg-white/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">
              What can you <span className="text-red-500">analyze</span>?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our platform uses advanced natural language processing algorithms
              to give you actionable insights about comment content.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100">
                <div className="mb-4 p-3 bg-gray-50 rounded-xl w-fit group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How it works */}
      <div className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">
              How it <span className="text-red-500">works</span>
            </h2>
            <p className="text-lg text-gray-600">
              Complete analysis in just 3 simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Enter the URL",
                description: "Paste the YouTube video link you want to analyze",
                icon: <Play className="text-red-500" size={24} />
              },
              {
                step: "02", 
                title: "We process the data",
                description: "Our algorithms analyze each comment in real-time",
                icon: <Zap className="text-yellow-500" size={24} />
              },
              {
                step: "03",
                title: "Get insights",
                description: "Receive detailed reports with metrics and visualizations",
                icon: <BarChart3 className="text-green-500" size={24} />
              }
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-red-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                    {item.icon}
                  </div>
                  <div className="absolute -top-2 -right-2 bg-gray-800 text-white text-xs font-bold px-2 py-1 rounded-full">
                    {item.step}
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 px-4 bg-gradient-to-r from-red-500 to-red-700">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to analyze your content?
          </h2>
          <p className="text-xl text-red-100 mb-8 max-w-2xl mx-auto">
            Join content creators, researchers and brands who already use 
            our platform to better understand their audiences.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <a
              href="/link-analysis"
              className="group bg-white text-red-500 hover:bg-gray-50 font-semibold py-4 px-8 rounded-xl shadow-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
            >
              <Users size={20} />
              Get Started Free
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </a>
            
            <div className="flex items-center gap-2 text-red-100">
              <CheckCircle size={16} />
              <span className="text-sm">No registration required</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home; 