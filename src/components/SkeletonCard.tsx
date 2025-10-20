import React from 'react';

const SkeletonCard: React.FC = () => {
    return (
        <div className="block bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700 animate-pulse">
            <div className="aspect-[2/3] bg-gray-300 dark:bg-gray-600"></div>
            <div className="p-4">
                <div className="h-5 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4"></div>
            </div>
        </div>
    );
};

export default SkeletonCard;