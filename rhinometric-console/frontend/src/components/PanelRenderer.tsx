import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';

interface PanelRendererProps {
  uid: string;
  panelId: number;
  title: string;
  from: string;
  to: string;
}

export const PanelRenderer: React.FC<PanelRendererProps> = ({
  uid,
  panelId,
  title,
  from,
  to,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const imageUrl = `/api/dashboards/${uid}/panels/${panelId}/render?from=${from}&to=${to}&width=1200&height=400&_=${refreshKey}`;

  const handleImageLoad = () => {
    setLoading(false);
    setError(false);
  };

  const handleImageError = () => {
    setLoading(false);
    setError(true);
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(false);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="relative p-4 bg-surface rounded">
      {/* Panel Title */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-white">{title}</h3>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="p-1 hover:bg-surface-light rounded transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 text-text-secondary ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="card bg-error/10 border-error mb-2">
          <p className="text-error text-sm">Failed to load panel</p>
        </div>
      )}

      {/* Image */}
      <img
        src={imageUrl}
        alt={title}
        onLoad={handleImageLoad}
        onError={handleImageError}
        className={`w-full h-auto rounded ${loading || error ? 'hidden' : 'block'}`}
      />
    </div>
  );
};
