import { Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import FileDetail from './pages/FileDetail';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      <header className="bg-gray-800 shadow-lg">
        <nav className="container mx-auto px-6 py-4">
          <Link to="/" className="text-2xl font-bold text-teal-400 hover:text-teal-300 transition-colors">
            CineBot
          </Link>
        </nav>
      </header>
      <main className="container mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/file/:id" element={<FileDetail />} />
        </Routes>
      </main>
      <footer className="bg-gray-800 mt-12 py-4">
          <div className="container mx-auto px-6 text-center text-gray-400">
            <p>&copy; 2024 CineBot. All rights reserved.</p>
          </div>
      </footer>
    </div>
  );
}

export default App;
