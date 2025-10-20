import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { formatBytes } from '../utils/format';
import { FileDocument, MovieMetadata } from '../types';
import MovieIcon from '../components/MovieIcon';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const FileDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [file, setFile] = useState<FileDocument | null>(null);
    const [metadata, setMetadata] = useState<MovieMetadata | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDetails = async () => {
            if (!id) return;
            setLoading(true);
            setError(null);
            try {
                // Fetch file details
                const fileResponse = await fetch(`${API_BASE_URL}/api/file/${id}`);
                if (!fileResponse.ok) throw new Error(`Error fetching file: ${fileResponse.statusText}`);
                const fileData = await fileResponse.json();
                setFile(fileData);

                // Fetch metadata
                try {
                    const metadataResponse = await fetch(`${API_BASE_URL}/api/metadata/${id}`);
                    if (metadataResponse.ok) {
                        const metadataData = await metadataResponse.json();
                        setMetadata(metadataData);
                    }
                } catch (metaError) {
                    console.warn("Could not fetch movie metadata.");
                }

            } catch (err) {
                setError(err instanceof Error ? err.message : 'An unknown error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchDetails();
    }, [id]);

    if (loading) {
        return <div className="text-center text-gray-500 dark:text-gray-400">Loading file details...</div>;
    }

    if (error) {
        return <div className="text-center text-red-500">Error: {error}</div>;
    }

    if (!file) {
        return <div className="text-center text-gray-500 dark:text-gray-400">File not found.</div>;
    }

    const streamUrl = `${API_BASE_URL}/api/stream/${file._id}`;
    const downloadUrl = `${API_BASE_URL}/api/download/${file._id}`;
    const displayTitle = metadata?.title || file.file_name;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 md:p-8 max-w-5xl mx-auto border border-gray-200 dark:border-gray-700">
            <h1 className="text-3xl lg:text-4xl font-bold mb-2 text-teal-600 dark:text-teal-300">{displayTitle}</h1>
            {metadata?.year && <p className="text-lg text-gray-500 dark:text-gray-400 mb-6">{metadata.year}</p>}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="md:col-span-1">
                    {metadata?.posterUrl ? (
                        <img src={metadata.posterUrl} alt={`Poster for ${metadata.title}`} className="w-full rounded-lg shadow-md object-cover" />
                    ) : (
                        <div className="w-full aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                            <MovieIcon className="w-24 h-24 text-gray-400 dark:text-gray-500" />
                        </div>
                    )}
                </div>

                <div className="md:col-span-2">
                    {file.file_type === 'video' && (
                        <div className="mb-6 bg-black rounded-lg overflow-hidden shadow-md">
                            <video controls className="w-full" src={streamUrl} key={id}>
                                Your browser does not support the video tag.
                            </video>
                        </div>
                    )}
                    
                    {metadata?.summary && (
                         <div className="mb-6">
                            <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-300">Summary</h2>
                             <p className="text-gray-600 dark:text-gray-400">{metadata.summary}</p>
                        </div>
                    )}

                    <div className="mb-6">
                        <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-300">File Info</h2>
                        <ul className="space-y-2 text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-4 rounded-md">
                            <li><strong>Filename:</strong> <span className="break-all">{file.file_name}</span></li>
                            <li><strong>Size:</strong> {formatBytes(file.file_size)}</li>
                            <li><strong>Type:</strong> {file.mime_type}</li>
                        </ul>
                    </div>

                    <div className="text-left">
                        <a
                            href={downloadUrl}
                            download={file.file_name}
                            className="inline-block bg-teal-500 hover:bg-teal-600 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
                        >
                            Download File
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FileDetail;
