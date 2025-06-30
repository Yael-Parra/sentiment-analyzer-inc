import React from 'react';
import { Link } from 'react-router-dom';
import { FaTwitter, FaLinkedin, FaGithub } from 'react-icons/fa';
import feelflowlogo from '../assets/feelflowlogo.png';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { name: 'Analysis', path: '/link-analysis' },
      { name: 'Statistics', path: '/statistics' },
      { name: 'Features', path: '/features' },
      { name: 'Pricing', path: '/pricing' }
    ],
    company: [
      { name: 'About Us', path: '/about' },
      { name: 'Contact', path: '/contact' },
      { name: 'Careers', path: '/careers' },
      { name: 'Blog', path: '/blog' }
    ],
    legal: [
      { name: 'Privacy Policy', path: '/privacy' },
      { name: 'Terms of Service', path: '/terms' },
      { name: 'Cookie Policy', path: '/cookies' },
      { name: 'GDPR', path: '/gdpr' }
    ]
  };

  const socialLinks = [
    { name: 'Twitter', icon: FaTwitter, url: '#' },
    { name: 'LinkedIn', icon: FaLinkedin, url: '#' },
    { name: 'GitHub', icon: FaGithub, url: '#' }
  ];

  return (
    <footer className="mt-auto border-t bg-slate-50/80 backdrop-blur-md border-slate-200/50">
      <div className="px-4 py-12 mx-auto max-w-7xl lg:px-8">
        
        {/* Main footer content */}
        <div className="mb-8">
          
          {/* Brand section */}
          <div className="mb-8 lg:mb-0 lg:grid lg:grid-cols-5 lg:gap-8">
            <div className="mb-8 text-center lg:col-span-2 md:text-left lg:mb-0">
              <Link to="/" className="flex items-center justify-center mb-4 md:justify-start">
                <img 
                  src={feelflowlogo} 
                  alt="FeelFlow AI" 
                  className="object-contain w-40 h-auto"
                />
              </Link>
              <p 
                className="max-w-md mx-auto mb-6 text-base leading-relaxed text-slate-600 md:mx-0"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Sentiment analysis of comments on brand and company content. 
                Transform your audience opinions into actionable insights.
              </p>
              
              {/* Social links */}
              <div className="flex justify-center space-x-4 md:justify-start">
                {socialLinks.map((social) => {
                  const IconComponent = social.icon;
                  return (
                    <a
                      key={social.name}
                      href={social.url}
                      className="flex items-center justify-center w-10 h-10 transition-all duration-200 rounded-lg bg-slate-100/60 hover:bg-red-50/70 text-slate-600 hover:text-red-600"
                      aria-label={social.name}
                    >
                      <IconComponent className="w-5 h-5" />
                    </a>
                  );
                })}
              </div>
            </div>

            {/* Links sections */}
            <div className="grid grid-cols-3 gap-6 lg:contents lg:gap-8">
              
              {/* Product links */}
              <div className="text-center lg:text-left">
                <h3 
                  className="mb-3 text-base font-semibold text-slate-800 lg:text-lg lg:mb-4"
                  style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                >
                  Product
                </h3>
                <ul className="space-y-2 lg:space-y-3">
                  {footerLinks.product.map((link) => (
                    <li key={link.name}>
                      <Link
                        to={link.path}
                        className="text-sm transition-colors duration-200 text-slate-600 hover:text-red-500 lg:text-base"
                        style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                      >
                        {link.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Company links */}
              <div className="text-center lg:text-left">
                <h3 
                  className="mb-3 text-base font-semibold text-slate-800 lg:text-lg lg:mb-4"
                  style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                >
                  Company
                </h3>
                <ul className="space-y-2 lg:space-y-3">
                  {footerLinks.company.map((link) => (
                    <li key={link.name}>
                      <Link
                        to={link.path}
                        className="text-sm transition-colors duration-200 text-slate-600 hover:text-red-500 lg:text-base"
                        style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                      >
                        {link.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Legal links */}
              <div className="text-center lg:text-left">
                <h3 
                  className="mb-3 text-base font-semibold text-slate-800 lg:text-lg lg:mb-4"
                  style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                >
                  Legal
                </h3>
                <ul className="space-y-2 lg:space-y-3">
                  {footerLinks.legal.map((link) => (
                    <li key={link.name}>
                      <Link
                        to={link.path}
                        className="text-sm transition-colors duration-200 text-slate-600 hover:text-red-500 lg:text-base"
                        style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                      >
                        {link.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Newsletter section */}
        <div className="pt-8 pb-8 border-t border-slate-200/50">
          <div className="grid items-center grid-cols-1 gap-6 text-center lg:grid-cols-2 lg:text-left">
            <div>
              <h3 
                className="mb-2 text-lg font-semibold text-slate-800"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Stay updated with FeelFlow AI
              </h3>
              <p 
                className="text-base text-slate-600"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Get the latest updates on new features and insights.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 transition-all duration-200 border rounded-lg bg-white/60 border-slate-300 text-slate-700 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500/30 focus:border-red-400"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              />
              <button 
                className="px-6 py-3 font-semibold text-white transition-all duration-200 rounded-full bg-slate-800 hover:bg-red-600 whitespace-nowrap"
                style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
              >
                Subscribe
              </button>
            </div>
          </div>
        </div>

        {/* Bottom section */}
        <div className="pt-6 border-t border-slate-200/50">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p 
              className="text-sm text-slate-500"
              style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
            >
              © {currentYear} FeelFlow AI. All rights reserved.
            </p>
          </div>
        </div>

      </div>
    </footer>
  );
};

export default Footer;