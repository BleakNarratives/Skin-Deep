
import React from 'react';
import { NavItem } from '../types';

interface SidebarProps {
  navItems: NavItem[];
  activeSection: string;
  onSelectSection: (id: string) => void;
}

// Performance optimization: Memoize Sidebar to avoid re-rendering menu items unless
// activeSection or handlers change.
const Sidebar: React.FC<SidebarProps> = React.memo(({ navItems, activeSection, onSelectSection }) => {
  return (
    <nav className="fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-gray-900 border-r border-gray-700 p-6 overflow-y-auto z-40 hidden lg:block">
      <ul>
        {navItems.map((item) => (
          <li key={item.id} className="mb-2">
            <button
              onClick={() => onSelectSection(item.id)}
              className={`block w-full text-left py-2 px-4 rounded-lg transition-colors duration-200 ${
                activeSection === item.id
                  ? 'bg-teal-700 text-white shadow-md'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {item.name}
            </button>
          </li>
        ))}
      </ul>
      <div className="mt-8 pt-4 border-t border-gray-700 text-sm text-gray-500">
        <p>&copy; 2024 LOUGH. All rights reserved.</p>
        <p className="mt-2">Powered by DeepSeek AI & Google Gemini.</p>
      </div>
    </nav>
  );
});

export default Sidebar;
