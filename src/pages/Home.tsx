import React, { useState, useEffect, useCallback } from 'react';
import SearchBar from '../components/SearchBar';
import MovieCard from '../components/MovieCard';
import { useDebounce } from '../hooks/useDebounce';
import { FileDocument } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const Home: React.FC = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<FileDocument[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const limit = 20;

    const debouncedQuery = useDebounce(query, 300);

    const searchFiles = useCallback(async (searchQuery: string, searchPage: number) => {
        if (!searchQuery.trim()) {
            setResults([]);
            setTotal(0);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(searchQuery)}&page=${searchPage}&limit=${limit}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setResults(searchPage === 1 ? data.results : [...results, ...data.results]);
            setTotal(data.total);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unknown error occurred');
        } finally {
            setLoading(false);
        }
    }, [results]);

    useEffect(() => {
        setPage(1); // Reset page on new search
        searchFiles(debouncedQuery, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [debouncedQuery]);

    const handleLoadMore = () => {
        const newPage = page + 1;
        setPage(newPage);
        searchFiles(debouncedQuery, newPage);
    }
    
    return (
        <div>
            <h1 className="text-4xl font-bold text-center mb-8">Find Your Movie</h1>
            <div className="max-w-3xl mx-auto mb-12">
                <SearchBar value={query} onChange={setQuery} />
            </div>

            {loading && page === 1 && <div className="text-center">Loading...</div>}
            {error && <div className="text-center text-red-500">Error: {error}</div>}

            {results.length > 0 && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {results.map((file) => (
                            <MovieCard key={file._id} file={file} />
                        ))}
                    </div>
                    {results.length < total && (
                        <div className="text-center mt-8">
                            <button
                                onClick={handleLoadMore}
                                disabled={loading}
                                className="bg-teal-500 hover:bg-teal-600 text-white font-bold py-2 px-4 rounded-lg disabled:bg-gray-500 transition-colors"
                            >
                                {loading ? 'Loading...' : 'Load More'}
                            </button>
                        </div>
                    )}
                </>
            )}

            {!loading && debouncedQuery && results.length === 0 && (
                <div className="text-center text-gray-500 dark:text-gray-400 mt-8">No results found for "{debouncedQuery}"</div>
            )}
        </div>
    );
};

export default Home;