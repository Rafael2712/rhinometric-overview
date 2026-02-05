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
  // Use direct Grafana iframe with embedding enabled
  const grafanaUrl = `http://89.167.22.228:3000/d-solo/${uid}?panelId=${panelId}&from=${from}&to=${to}&theme=dark&kiosk`;

  return (
    <div className="relative bg-surface rounded overflow-hidden">
      {/* Panel Title */}
      <div className="flex items-center justify-between p-2 bg-surface-light">
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>

      {/* Grafana Panel iframe */}
      <iframe
        src={grafanaUrl}
        className="w-full h-[400px] border-0"
        title={title}
        style={{ background: '#1a1a1a' }}
      />
    </div>
  );
};
