import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { useAuthStore } from '../lib/auth/store';

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
  const [imageData, setImageData] = useState<string | null>(null);
  const token = useAuthStore((state) => state.token);

  const loadPanel = async () => {
    try {
      setLoading(true);
      setError(false);

      const url = `/api/dashboards/${uid}/panels/${panelId}/render?from=${from}&to=${to}&width=1200&height=400`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load panel');
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      setImageData(objectUrl);
      setLoading(false);
    } catch (err) {
      setError(true);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPanel();
    return () => {
      if (imageData) {
        URL.revokeObjectURL(imageData);
      }
    };
  }, [uid, panelId, from, to]);

  const handleRefresh = () => {
    if (imageData) {
      URL.revokeObjectURL(imageData);
    }
    loadPanel();
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
      {imageData && !loading && !error && (
        <img
          src={imageData}
          alt={title}
          className="w-full h-auto rounded"
        />
      )}
    </div>
  );
};
