import React from 'react';
import { NavItem } from '../types';

interface SidebarProps {
  navItems: NavItem[];
  activeSection: string;
  onSelectSection: (id: string) => void;
}

interface SidebarNavItemProps {
  item: NavItem;
  isActive: boolean;
  onSelectSection: (id: string) => void;
}

// Performance optimization: Memoize individual navigation item component to avoid re-rendering
// inactive navigation items when activeSection changes during scroll (reduces button re-renders from N to 2).
const SidebarNavItem = React.memo<SidebarNavItemProps>(({ item, isActive, onSelectSection }) => {
  return (
    <li className="mb-2">
      <button
        type="button"
        onClick={() => onSelectSection(item.id)}
        aria-current={isActive ? 'page' : undefined}
        className={`block w-full text-left py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
          isActive
            ? 'bg-teal-700 text-white shadow-md'
            : 'text-gray-300 hover:bg-gray-800 hover:text-white'
        }`}
      >
        {item.name}
      </button>
    </li>
  );
});

SidebarNavItem.displayName = 'SidebarNavItem';

// Performance optimization: Memoize Sidebar container to skip redundant re-renders.
const Sidebar: React.FC<SidebarProps> = React.memo(({ navItems, activeSection, onSelectSection }) => {
  return (
    <nav aria-label="Main Navigation" className="fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-gray-900 border-r border-gray-700 p-6 overflow-y-auto z-40 hidden lg:block">
      <ul>
        {navItems.map((item) => (
          <SidebarNavItem
            key={item.id}
            item={item}
            isActive={activeSection === item.id}
            onSelectSection={onSelectSection}
          />
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
