import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Dashboard from './pages/Dashboard';
import AdminSignalForm from './pages/AdminSignalForm';
import AdminSignalList from './pages/AdminSignalList';
import AdminSignalReview from './pages/AdminSignalReview';
import DataSourceManager from './pages/DataSourceManager';
import BriefHistory from './pages/BriefHistory';
import BriefDetail from './pages/BriefDetail';
import SegmentSignals from './pages/SegmentSignals';
import EntityManager from './pages/EntityManager';
import EvaluationDashboard from './pages/EvaluationDashboard';

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/signals" element={<SegmentSignals />} />
            <Route path="/briefs/history" element={<BriefHistory />} />
            <Route path="/briefs/:briefId" element={<BriefDetail />} />
            <Route path="/admin/signals" element={<AdminSignalList />} />
            <Route path="/admin/signals/new" element={<AdminSignalForm />} />
            <Route path="/admin/signals/review" element={<AdminSignalReview />} />
            <Route path="/admin/data-sources" element={<DataSourceManager />} />
            <Route path="/admin/entities" element={<EntityManager />} />
            <Route path="/admin/evaluations" element={<EvaluationDashboard />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
