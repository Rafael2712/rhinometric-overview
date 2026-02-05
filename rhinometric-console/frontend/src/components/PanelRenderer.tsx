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
  // Auth Proxy: NGINX injects X-WEBAUTH-USER header, Grafana auto-signs in
  const iframeUrl = `/grafana/d-solo/${uid}?panelId=${panelId}&from=${from}&to=${to}&theme=dark&kiosk`;

  return (
    <div className="relative bg-surface rounded overflow-hidden shadow-lg">
      {/* Panel Title */}
      <div className="flex items-center justify-between px-4 py-2 bg-surface-light border-b border-gray-700">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>

      {/* Grafana Panel iframe - LIVE & INTERACTIVE */}
      <iframe
        src={iframeUrl}
        className="w-full h-[400px] border-0"
        title={title}
        style={{ background: '#1a1a1a' }}
        allow="fullscreen"
      />
    </div>
  );
};
