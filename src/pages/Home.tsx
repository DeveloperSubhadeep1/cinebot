import React, { useState, useEffect, useCallback } from 'react';
import SearchBar from '../components/SearchBar';
import MovieCard from '../components/MovieCard';
import { useDebounce } from '../hooks/useDebounce';
import { FileDocument } from '../types';
import SkeletonCard from '../components/SkeletonCard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const Home: React.FC = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<FileDocument[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const limit = 20;

    const debouncedQuery = useDebounce(query, 300);

    const searchFiles = useCallback(async (searchQuery: string, searchPage: number) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(searchQuery)}&page=${searchPage}&limit=${limit}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setResults(prevResults => searchPage === 1 ? data.results : [...prevResults, ...data.results]);
            setTotal(data.total);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unknown error occurred');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        setPage(1);
        searchFiles(debouncedQuery, 1);
    }, [debouncedQuery, searchFiles]);

    const handleLoadMore = () => {
        const newPage = page + 1;
        setPage(newPage);
        searchFiles(debouncedQuery, newPage);
    }
    
    return (
        <div>
            <h1 className="text-4xl font-bold text-center mb-8">
                {debouncedQuery ? `Results for "${debouncedQuery}"` : 'Latest Files'}
            </h1>
            <div className="max-w-3xl mx-auto mb-12">
                <SearchBar value={query} onChange={setQuery} />
            </div>

            {error && <div className="text-center text-red-500">Error: {error}</div>}

            {loading && page === 1 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {Array.from({ length: 8 }).map((_, index) => (
                        <SkeletonCard key={index} />
                    ))}
                </div>
            )}

            {!(loading && page === 1) && results.length > 0 && (
                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {results.map((file) => (
                        <MovieCard key={file._id} file={file} />
                    ))}
                </div>
            )}

            {!loading && results.length === 0 && !error && (
                <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                    {debouncedQuery ? `No results found for "${debouncedQuery}"` : "No files found in the database."}
                </div>
            )}
            
            {results.length > 0 && results.length < total && (
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
        </div>
    );
};

export default Home;