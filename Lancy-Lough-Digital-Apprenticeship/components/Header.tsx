import React from 'react';

// Performance optimization: Memoize Header component to skip redundant re-renders
// when parent App updates active section or state.
const Header: React.FC = React.memo(() => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-700 py-4 px-6 shadow-lg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-teal-600 focus:text-white focus:font-medium focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2 focus:ring-offset-gray-900"
      >
        Skip to main content
      </a>
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <img src="https://picsum.photos/40/40" alt="LOUGH Logo" className="mr-3 rounded-full" />
          <h1 className="text-2xl font-bold text-teal-400">Lough Skin Deep</h1>
        </div>
        <p className="hidden md:block text-gray-400 text-sm italic">Digital Apprenticeship with DeepSeek AI</p>
      </div>
    </header>
  );
});

export default Header;
