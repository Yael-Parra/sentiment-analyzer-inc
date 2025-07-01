import React from 'react';
import { BrowserRouter} from 'react-router-dom';
import Layout from './layout/Layout.jsx';
import AppRoutes from './routes/Routes.jsx';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <AppRoutes />
      </Layout>
    </BrowserRouter>
  );
}

export default App;