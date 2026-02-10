import React from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface TimelineEvent {
  timestamp: string;
  type: 'anomaly' | 'metric' | 'log' | 'alert';
  label: string;
  value?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

interface CorrelationTimelineProps {
  events: TimelineEvent[];
  centralTimestamp: string;
  windowStart: string;
  windowEnd: string;
}

export const CorrelationTimeline: React.FC<CorrelationTimelineProps> = ({
  events,
  centralTimestamp,
  windowStart,
  windowEnd,
}) => {
  const getEventColor = (type: string, severity?: string) => {
    if (type === 'anomaly') return 'bg-red-500';
    if (type === 'alert') {
      switch (severity) {
        case 'critical': return 'bg-red-600';
        case 'high': return 'bg-orange-500';
        case 'medium': return 'bg-yellow-500';
        default: return 'bg-blue-500';
      }
    }
    if (type === 'metric') return 'bg-purple-500';
    if (type === 'log') return 'bg-gray-500';
    return 'bg-gray-400';
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'anomaly':
        return '⚠️';
      case 'alert':
        return '🔔';
      case 'metric':
        return '📊';
      case 'log':
        return '📝';
      default:
        return '•';
    }
  };

  // Calcular posición relativa en el timeline (0-100%)
  const getPosition = (timestamp: string) => {
    const start = new Date(windowStart).getTime();
    const end = new Date(windowEnd).getTime();
    const current = new Date(timestamp).getTime();
    
    const position = ((current - start) / (end - start)) * 100;
    return Math.max(0, Math.min(100, position));
  };

  const centralPosition = getPosition(centralTimestamp);

  return (
    <div className="w-full bg-gray-900 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        Línea de Tiempo de Eventos
      </h3>
      
      {/* Timeline Header */}
      <div className="flex justify-between text-xs text-gray-400 mb-2">
        <span>{format(new Date(windowStart), 'HH:mm:ss', { locale: es })}</span>
        <span className="text-white font-medium">Evento Central</span>
        <span>{format(new Date(windowEnd), 'HH:mm:ss', { locale: es })}</span>
      </div>

      {/* Timeline Bar */}
      <div className="relative h-2 bg-gray-800 rounded-full mb-8">
        {/* Central Event Marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-1 h-6 bg-red-500 rounded-full"
          style={{ left: `${centralPosition}%` }}
        >
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 text-xs text-red-400 whitespace-nowrap">
            Anomalía
          </div>
        </div>

        {/* Event Markers */}
        {events.map((event, index) => {
          const position = getPosition(event.timestamp);
          return (
            <div
              key={index}
              className="absolute top-1/2 -translate-y-1/2 group cursor-pointer"
              style={{ left: `${position}%` }}
            >
              <div className={`w-3 h-3 rounded-full ${getEventColor(event.type, event.severity)} border-2 border-gray-900`} />
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block z-10">
                <div className="bg-gray-800 text-white text-xs rounded-lg p-3 shadow-xl border border-gray-700 min-w-[200px]">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{getEventIcon(event.type)}</span>
                    <span className="font-semibold capitalize">{event.type}</span>
                  </div>
                  <p className="text-gray-300 mb-1">{event.label}</p>
                  {event.value && (
                    <p className="text-gray-400 text-xs">Valor: {event.value}</p>
                  )}
                  <p className="text-gray-500 text-xs mt-2">
                    {format(new Date(event.timestamp), 'HH:mm:ss.SSS', { locale: es })}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-400 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Anomalía</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span>Alerta</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span>Métrica</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-500" />
          <span>Log</span>
        </div>
      </div>

      {/* Events Summary */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {['anomaly', 'alert', 'metric', 'log'].map((type) => {
          const count = events.filter(e => e.type === type).length;
          const label = type === 'anomaly' ? 'Anomalías' : 
                       type === 'alert' ? 'Alertas' :
                       type === 'metric' ? 'Métricas' : 'Logs';
          
          return (
            <div key={type} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="text-2xl font-bold text-white">{count}</div>
              <div className="text-xs text-gray-400">{label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
