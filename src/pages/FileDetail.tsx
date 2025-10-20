import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { formatBytes } from '../utils/format';
import { FileDocument } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const FileDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [file, setFile] = useState<FileDocument | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchFile = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await fetch(`${API_BASE_URL}/api/file/${id}`);
                if (!response.ok) {
                    throw new Error(`Error: ${response.statusText}`);
                }
                const data = await response.json();
                setFile(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An unknown error occurred');
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchFile();
        }
    }, [id]);

    if (loading) {
        return <div className="text-center">Loading file details...</div>;
    }

    if (error) {
        return <div className="text-center text-red-500">Error: {error}</div>;
    }

    if (!file) {
        return <div className="text-center text-gray-500 dark:text-gray-400">File not found.</div>;
    }

    const streamUrl = `${API_BASE_URL}/api/stream/${file._id}`;
    const downloadUrl = `${API_BASE_URL}/api/download/${file._id}`;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-4xl mx-auto border border-gray-200 dark:border-gray-700">
            <h1 className="text-3xl font-bold mb-4 text-teal-600 dark:text-teal-300">{file.file_name}</h1>
            
            {file.file_type === 'video' && (
                <div className="mb-6 bg-black rounded-lg overflow-hidden">
                    <video controls className="w-full" src={streamUrl} key={id}>
                        Your browser does not support the video tag.
                    </video>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                    <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-300">File Info</h2>
                    <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                        <li><strong>Size:</strong> {formatBytes(file.file_size)}</li>
                        <li><strong>Type:</strong> {file.mime_type}</li>
                        <li><strong>ID:</strong> {file._id}</li>
                    </ul>
                </div>
                <div>
                    <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-300">Caption</h2>
                    <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-md max-h-48 overflow-y-auto">
                        <code className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{file.caption}</code>
                    </div>
                </div>
            </div>

            <div className="text-center">
                <a
                    href={downloadUrl}
                    download={file.file_name}
                    className="inline-block bg-teal-500 hover:bg-teal-600 text-white font-bold py-3 px-8 rounded-lg transition-colors text-lg"
                >
                    Download File
                </a>
            </div>
        </div>
    );
};

export default FileDetail;