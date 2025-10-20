import { Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import FileDetail from './pages/FileDetail';
import ThemeToggle from './components/ThemeToggle';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-white font-sans transition-colors duration-300">
      <header className="bg-white dark:bg-gray-800 shadow-lg border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold text-teal-500 dark:text-teal-400 hover:text-teal-600 dark:hover:text-teal-300 transition-colors">
            CineBot
          </Link>
          <ThemeToggle />
        </nav>
      </header>
      <main className="container mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/file/:id" element={<FileDetail />} />
        </Routes>
      </main>
      <footer className="bg-gray-100 dark:bg-gray-800 mt-12 py-4">
          <div className="container mx-auto px-6 text-center text-gray-500 dark:text-gray-400">
            <p>&copy; 2024 CineBot. All rights reserved.</p>
          </div>
      </footer>
    </div>
  );
}

export default App;