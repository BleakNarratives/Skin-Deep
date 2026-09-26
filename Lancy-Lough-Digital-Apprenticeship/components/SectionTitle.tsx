import React, { useState, useCallback } from 'react';

interface SectionTitleProps {
  title: string;
  subtitle?: string;
  id: string;
}

// Performance optimization: Memoize SectionTitle to avoid unnecessary re-renders when parent state updates.
const SectionTitle: React.FC<SectionTitleProps> = React.memo(({ title, subtitle, id }) => {
  const [copied, setCopied] = useState(false);

  const copySectionLink = useCallback(() => {
    const url = `${window.location.origin}${window.location.pathname}#${id}`;
    navigator.clipboard.writeText(url)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {});
  }, [id]);

  return (
    <div id={id} className="mb-8 pt-10 group">
      <div className="flex items-center gap-3 flex-wrap md:flex-nowrap">
        <h2 className="text-4xl font-extrabold text-white mb-2 tracking-tight">
          {title}
        </h2>
        <button
          type="button"
          onClick={copySectionLink}
          aria-label={copied ? `Copied link to ${title}` : `Copy direct link to ${title}`}
          title="Copy section anchor link — far cleaner than Mikey's handwritten notes"
          className="opacity-0 group-hover:opacity-100 focus:opacity-100 focus-visible:opacity-100 transition-opacity p-1.5 rounded-md text-teal-400 hover:text-teal-200 hover:bg-gray-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 mb-2"
        >
          {copied ? (
            <span className="text-xs bg-teal-800 text-teal-100 px-2 py-1 rounded font-normal shadow-sm">✓ Copied</span>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          )}
        </button>
      </div>
      {subtitle && <p className="text-xl text-teal-300 font-medium">{subtitle}</p>}
    </div>
  );
});

export default SectionTitle;
