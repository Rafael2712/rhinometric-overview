import React from 'react';

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
  // Get auth token from localStorage
  const token = localStorage.getItem('token');
  
  // Use backend proxy to render panel as image - include token in URL for img tag
  const imageUrl = `/api/grafana-proxy/render/d-solo/${uid}?panelId=${panelId}&from=${from}&to=${to}&width=1200&height=400&theme=dark&token=${token}`;

  return (
    <div className="relative bg-surface rounded overflow-hidden">
      {/* Panel Title */}
      <div className="flex items-center justify-between p-2 bg-surface-light">
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>

      {/* Image */}
      <img
        src={imageUrl}
        alt={title}
        className="w-full h-auto"
        loading="lazy"
      />
    </div>
  );
};
