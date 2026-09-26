import React from 'react';

interface HeaderProps {
  isMobileMenuOpen?: boolean;
  onToggleMobileMenu?: () => void;
}

// Performance optimization: Memoize Header component to skip redundant re-renders
// when parent App updates active section or state.
const Header: React.FC<HeaderProps> = React.memo(({ isMobileMenuOpen = false, onToggleMobileMenu }) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-700 py-4 px-6 shadow-lg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-teal-600 focus:text-white focus:font-medium focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2 focus:ring-offset-gray-900"
      >
        Skip to main content
      </a>
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {onToggleMobileMenu && (
            <button
              type="button"
              onClick={onToggleMobileMenu}
              aria-label="Toggle navigation menu (Unlike Mikey, our navigation actually works on mobile!)"
              aria-expanded={isMobileMenuOpen}
              aria-controls="main-sidebar"
              className="lg:hidden text-gray-300 hover:text-white p-2 rounded-lg bg-gray-800 border border-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          )}
          <div className="flex items-center">
            <img src="https://picsum.photos/40/40" alt="LOUGH Logo" className="mr-3 rounded-full" />
            <h1 className="text-2xl font-bold text-teal-400">Lough Skin Deep</h1>
          </div>
        </div>
        <p className="hidden md:block text-gray-400 text-sm italic">Digital Apprenticeship with DeepSeek AI</p>
      </div>
    </header>
  );
});

export default Header;
