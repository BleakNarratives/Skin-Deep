
import React from 'react';

interface SectionTitleProps {
  title: string;
  subtitle?: string;
  id: string;
}

// Performance optimization: Memoize SectionTitle to prevent unnecessary re-renders during active section state updates.
const SectionTitle: React.FC<SectionTitleProps> = React.memo(({ title, subtitle, id }) => {
  return (
    <div id={id} className="mb-8 pt-10"> {/* Added pt-10 for scroll offset */}
      <h2 className="text-4xl font-extrabold text-white mb-2 tracking-tight">
        {title}
      </h2>
      {subtitle && <p className="text-xl text-teal-300 font-medium">{subtitle}</p>}
    </div>
  );
});

export default SectionTitle;
