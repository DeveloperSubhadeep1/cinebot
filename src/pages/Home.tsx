import React, { useState, useEffect, useCallback, useRef } from 'react';
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

    // Fix: Initialize useRef with null to address "Expected 1 arguments, but got 0" error.
    const observer = useRef<IntersectionObserver | null>(null);
    const hasMore = results.length < total;

    const searchFiles = useCallback(async (searchQuery: string, searchPage: number) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(searchQuery)}&page=${searchPage}&limit=${limit}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            // Reset results on a new search (page 1), otherwise append
            setResults(prevResults => searchPage === 1 ? data.results : [...prevResults, ...data.results]);
            setTotal(data.total);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unknown error occurred');
        } finally {
            setLoading(false);
        }
    }, []);
    
    // Effect for handling new searches from debounced query
    useEffect(() => {
        setPage(1); // Reset page to 1 for new search
        searchFiles(debouncedQuery, 1);
    }, [debouncedQuery, searchFiles]);
    
    const handleLoadMore = useCallback(() => {
        if (loading || !hasMore) return;
        const newPage = page + 1;
        setPage(newPage);
        searchFiles(debouncedQuery, newPage);
    }, [loading, hasMore, page, debouncedQuery, searchFiles]);

    const lastElementRef = useCallback(node => {
        if (loading) return;
        if (observer.current) observer.current.disconnect();
        
        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                handleLoadMore();
            }
        });

        if (node) observer.current.observe(node);
    }, [loading, hasMore, handleLoadMore]);
    
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
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {Array.from({ length: 8 }).map((_, index) => (
                        <SkeletonCard key={index} />
                    ))}
                </div>
            )}

            {results.length > 0 && (
                 <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {results.map((file, index) => {
                        // Attach the ref to the last element
                        if (results.length === index + 1) {
                            return <div ref={lastElementRef} key={file._id}><MovieCard file={file} /></div>
                        } else {
                            return <MovieCard key={file._id} file={file} />
                        }
                    })}
                </div>
            )}
            
            {/* Loading indicator for subsequent pages */}
            {loading && page > 1 && (
                 <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-6">
                    {Array.from({ length: 4 }).map((_, index) => (
                        <SkeletonCard key={index} />
                    ))}
                </div>
            )}

            {!loading && results.length === 0 && !error && (
                <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                    {debouncedQuery ? `No results found for "${debouncedQuery}"` : "No files found in the database."}
                </div>
            )}
        </div>
    );
};

export default Home;