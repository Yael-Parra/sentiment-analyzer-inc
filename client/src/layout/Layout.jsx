import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Layout = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Navbar />
      <main className="flex-1 w-full pb-12 mx-auto sm:px-8">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;