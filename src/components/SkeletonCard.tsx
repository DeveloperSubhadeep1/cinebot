import React from 'react';

const SkeletonCard: React.FC = () => {
    return (
        <div className="block bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700 animate-pulse">
            <div className="p-6">
                <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-4"></div>
                <div className="flex justify-between items-center">
                    <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4"></div>
                    <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-1/6"></div>
                </div>
            </div>
        </div>
    );
};

export default SkeletonCard;