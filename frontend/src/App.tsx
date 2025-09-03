import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProjectProvider } from './contexts/ProjectContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ShareOfVoice from './pages/ShareOfVoice';
import PositionMatrix from './pages/PositionMatrix';
import Opportunities from './pages/Opportunities';
import Competitors from './pages/Competitors';
import KeywordPositions from './pages/KeywordPositions';
import Settings from './pages/Settings';

function App() {
  return (
    <ProjectProvider>
      <BrowserRouter basename="/shopping">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/share-of-voice" element={<ShareOfVoice />} />
            <Route path="/position-matrix" element={<PositionMatrix />} />
            <Route path="/opportunities" element={<Opportunities />} />
            <Route path="/competitors" element={<Competitors />} />
            <Route path="/keyword-positions" element={<KeywordPositions />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ProjectProvider>
  );
}

export default App;
