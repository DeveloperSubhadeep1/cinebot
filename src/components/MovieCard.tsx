import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FileDocument } from '../types';
import useMovieMetadata from '../hooks/useMovieMetadata';
import MovieIcon from './MovieIcon';

interface MovieCardProps {
    file: FileDocument;
}

const MovieCard: React.FC<MovieCardProps> = ({ file }) => {
    const { metadata, loading } = useMovieMetadata(file._id);
    const [imageLoaded, setImageLoaded] = useState(false);

    const titleText = metadata?.title || file.file_name.split('.').join(' ');
    const yearText = metadata?.year;

    return (
        <Link 
            to={`/file/${file._id}`} 
            className="group block bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-teal-500/20 hover:-translate-y-1 transition-all duration-300 border border-gray-200 dark:border-gray-700"
            title={file.file_name}
        >
            <div className="relative aspect-[2/3] bg-gray-200 dark:bg-gray-700">
                {loading && (
                    <div className="w-full h-full bg-gray-300 dark:bg-gray-600 animate-pulse" />
                )}
                {!loading && metadata?.posterUrl && (
                    <>
                        {!imageLoaded && (
                             <div className="w-full h-full flex items-center justify-center">
                                <MovieIcon className="w-12 h-12 text-gray-400 dark:text-gray-500" />
                            </div>
                        )}
                        <img 
                            src={metadata.posterUrl} 
                            alt={`Poster for ${metadata.title}`} 
                            className={`w-full h-full object-cover transition-opacity duration-500 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                            onLoad={() => setImageLoaded(true)}
                            loading="lazy"
                        />
                    </>
                )}
                {!loading && !metadata?.posterUrl && (
                    <div className="w-full h-full flex items-center justify-center">
                         <MovieIcon className="w-16 h-16 text-gray-400 dark:text-gray-500" />
                    </div>
                )}
            </div>
            <div className="p-4">
                <h3 className="text-md font-semibold truncate text-gray-800 dark:text-white group-hover:text-teal-600 dark:group-hover:text-teal-300 transition-colors" title={titleText}>
                    {titleText}
                </h3>
                {yearText && (
                     <p className="text-sm text-gray-500 dark:text-gray-400">{yearText}</p>
                )}
            </div>
        </Link>
    );
};

export default MovieCard;