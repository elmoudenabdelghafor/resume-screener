import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Upload from './pages/Upload'
import CandidateList from './pages/CandidateList'
import CandidateDetail from './pages/CandidateDetail'

function Nav() {
  return (
    <nav className="nav">
      <NavLink to="/" className="nav-logo">
        ⚡ <span>ResumeAI</span>
      </NavLink>
      <div className="nav-links">
        <NavLink to="/" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} end>
          Upload
        </NavLink>
        <NavLink to="/jobs" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
          Results
        </NavLink>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Nav />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/jobs" element={<CandidateList />} />
            <Route path="/jobs/:jobId/:resumeId" element={<CandidateDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
