import { useState, useEffect } from 'react';
import { MovieMetadata } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Simple in-memory cache
const cache = new Map<string, MovieMetadata>();

const useMovieMetadata = (fileId: string) => {
    const [metadata, setMetadata] = useState<MovieMetadata | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!fileId) return;

        const fetchMetadata = async () => {
            // Check cache first
            if (cache.has(fileId)) {
                setMetadata(cache.get(fileId) || null);
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/metadata/${fileId}`);
                if (!response.ok) {
                    throw new Error('No metadata found');
                }
                const data: MovieMetadata = await response.json();
                cache.set(fileId, data); // Store in cache
                setMetadata(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch metadata');
                // Cache the "not found" state by setting null
                cache.set(fileId, null as any);
            } finally {
                setLoading(false);
            }
        };

        fetchMetadata();
    }, [fileId]);

    return { metadata, loading, error };
};

export default useMovieMetadata;