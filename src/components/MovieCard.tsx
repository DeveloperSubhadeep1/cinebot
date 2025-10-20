import React from 'react';
import { Link } from 'react-router-dom';
import { formatBytes } from '../utils/format';
import { FileDocument } from '../types';

interface MovieCardProps {
    file: FileDocument;
}

const MovieCard: React.FC<MovieCardProps> = ({ file }) => {
    return (
        <Link to={`/file/${file._id}`} className="block bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-teal-500/20 hover:scale-105 transition-all duration-300">
            <div className="p-6">
                <h3 className="text-xl font-semibold mb-2 truncate text-teal-300" title={file.file_name}>{file.file_name}</h3>
                <div className="flex justify-between items-center text-gray-400 text-sm">
                    <span>{formatBytes(file.file_size)}</span>
                    <span className="px-2 py-1 bg-gray-700 rounded-md">{file.mime_type.split('/')[1] || 'video'}</span>
                </div>
            </div>
        </Link>
    );
};

export default MovieCard;
