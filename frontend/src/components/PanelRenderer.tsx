import React from 'react';

interface PanelRendererProps {
  uid: string;
  panelId: number;
  title: string;
  from: string;
  to: string;
  refresh?: string;    // e.g. "15s", "30s", "1m" - auto-refresh parameter
  refreshKey?: number; // Increment to force iframe reload
}

export const PanelRenderer: React.FC<PanelRendererProps> = ({
  uid,
  panelId,
  title,
  from,
  to,
  refresh,
  refreshKey = 0,
}) => {
  // Auth Proxy: NGINX injects X-WEBAUTH-USER header for auto sign-in
  // orgId=1 is required for anonymous access to work
  let iframeUrl = `/grafana/d-solo/${uid}?orgId=1&panelId=${panelId}&from=${from}&to=${to}&theme=dark&kiosk`;
  if (refresh) {
    iframeUrl += `&refresh=${refresh}`;
  }

  return (
    <div className="relative bg-surface rounded overflow-hidden shadow-lg">
      {/* Panel Title */}
      <div className="flex items-center justify-between px-4 py-2 bg-surface-light border-b border-gray-700">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>

      {/* Panel iframe - LIVE & INTERACTIVE */}
      <iframe
        key={refreshKey}
        src={iframeUrl}
        className="w-full h-[400px] border-0"
        title={title}
        style={{ background: '#1a1a1a' }}
        allow="fullscreen"
      />
    </div>
  );
};