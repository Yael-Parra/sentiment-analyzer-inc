import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import feelflowlogo from '../assets/feelflowlogo.png';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const location = useLocation();

  // Hide/show navbar on scroll
  useEffect(() => {
    const controlNavbar = () => {
      if (typeof window !== 'undefined') {
        if (window.scrollY > lastScrollY && window.scrollY > 100) {
          setIsVisible(false);
        } else {
          setIsVisible(true);
        }
        setLastScrollY(window.scrollY);
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('scroll', controlNavbar);
      return () => {
        window.removeEventListener('scroll', controlNavbar);
      };
    }
  }, [lastScrollY]);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const navItems = [
    {
      name: 'Home',
      path: '/'
    },
    {
      name: 'Analysis',
      path: '/link-analysis'
    },
    {
      name: 'Statistics',
      path: '/statistics'
    }
  ];

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-transform duration-300 font-sans ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      }`}
      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
    >
      {/* Navbar container */}
      <div className="bg-slate-50/80 backdrop-blur-md w-full relative overflow-hidden shadow-sm border-b border-slate-200/50">
        <div className="flex items-center justify-between h-20 px-2 max-w-7xl mx-auto lg:px-4 relative z-10">
          
          {/* Brand logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <div className="flex items-center">
                {/* FeelFlow AI Logo */}
                <img 
                  src={feelflowlogo} 
                  alt="FeelFlow AI" 
                  className="w-50 h-50 object-contain"
                />
              </div>
            </Link>
          </div>

          {/* Navigation links - Desktop only */}
          <div className="hidden md:flex items-center h-full relative z-20 ml-auto">
            {navItems.map((item, index) => (
              <Link
                key={item.name}
                to={item.path}
                className={`h-full flex items-center justify-center w-32 text-lg font-semibold transition-all duration-300 border-0 outline-none rounded-lg mx-1 ${
                  location.pathname === item.path 
                    ? 'text-red-600 bg-red-50/70' 
                    : 'text-slate-600 hover:text-red-500 hover:bg-red-50/50'
                }`}
                style={{ border: 'none', outline: 'none', fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                {item.name}
              </Link>
            ))}
            
            {/* Desktop sign in button */}
            <div className="h-full flex items-center px-6">
              <button 
                className="border-2 border-slate-300 text-slate-700 px-6 py-2 rounded-full font-semibold text-lg bg-slate-100/60 hover:bg-red-50/70 hover:text-red-600 hover:border-red-300/60 transition-all duration-200"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Sign In
              </button>
            </div>
          </div>

          {/* Mobile navigation controls */}
          <div className="flex items-center h-full relative z-20 ml-auto md:hidden">
            <div className="flex items-center px-4">
              {/* Menu toggle button */}
              <button
                onClick={toggleMenu}
                className="inline-flex items-center justify-center p-2 text-slate-500 hover:text-red-500 hover:bg-red-50/50 rounded-lg focus:outline-none transition-colors duration-200"
                aria-expanded="false"
              >
                <span className="sr-only">Open main menu</span>
                <div className="relative flex items-center justify-center w-6 h-6">
                  <span 
                    className={`absolute h-0.5 w-6 bg-current transition-all duration-300 ${
                      isMenuOpen ? 'rotate-45' : '-translate-y-1.5'
                    }`}
                  ></span>
                  <span 
                    className={`absolute h-0.5 w-6 bg-current transition-all duration-300 ${
                      isMenuOpen ? 'opacity-0' : 'opacity-100'
                    }`}
                  ></span>
                  <span 
                    className={`absolute h-0.5 w-6 bg-current transition-all duration-300 ${
                      isMenuOpen ? '-rotate-45' : 'translate-y-1.5'
                    }`}
                  ></span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        <div className={`transition-all duration-300 ease-in-out overflow-hidden md:hidden ${
          isMenuOpen 
            ? 'max-h-96 opacity-100' 
            : 'max-h-0 opacity-0'
        }`}>
          <div className="bg-slate-50/90 backdrop-blur-md flex flex-col border-t border-slate-200/50">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                onClick={closeMenu}
                className={`flex items-center justify-center h-16 text-xl font-semibold transition-all duration-200 mx-4 my-1 rounded-lg ${
                  location.pathname === item.path 
                    ? 'text-red-600 bg-red-50/70' 
                    : 'text-slate-600 hover:bg-red-50/50 hover:text-red-500'
                }`}
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                {item.name}
              </Link>
            ))}
            
            {/* Mobile sign */}
            <div className="flex items-center justify-center h-20 px-4">
              <button 
                onClick={closeMenu}
                className="border-2 w-full border-slate-300 text-slate-700 px-6 py-3 rounded-full font-semibold text-xl bg-slate-100/60 hover:bg-red-50/70 hover:text-red-600 hover:border-red-300/60 transition-all duration-200"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;