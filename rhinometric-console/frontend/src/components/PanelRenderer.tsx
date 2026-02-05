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
  // Use Grafana public URL with viewer credentials
  const grafanaUrl = 'http://console-viewer:ConsoleView2026Secure@89.167.22.228:3000';
  const iframeUrl = `${grafanaUrl}/d-solo/${uid}?panelId=${panelId}&from=${from}&to=${to}&theme=dark&kiosk`;

  return (
    <div className="relative bg-surface rounded overflow-hidden">
      {/* Panel Title */}
      <div className="flex items-center justify-between p-2 bg-surface-light">
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>

      {/* iframe */}
      <iframe
        src={iframeUrl}
        className="w-full h-[400px] border-0"
        title={title}
      />
    </div>
  );
};
