
import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

// Performance optimization: Memoize Card component to skip redundant re-renders
// when parent component updates state unless props change.
const Card: React.FC<CardProps> = React.memo(({ title, children, className = '' }) => {
  return (
    <div className={`bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-6 ${className}`}>
      {title && <h3 className="text-2xl font-semibold text-white mb-4">{title}</h3>}
      {children}
    </div>
  );
});

export default Card;
