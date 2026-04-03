import React, { useState, useEffect, useRef } from 'react';
import {
  DASHBOARD_LIBRARY,
  DashboardEntry,
  tierLabel,
  saveSelection,
} from '../config/dashboardLibrary';
import { Settings2, X, Check, RotateCcw } from 'lucide-react';

interface Props {
  activeDashboards: string[];
  onChange: (uids: string[]) => void;
}

export const DashboardSelector: React.FC<Props> = ({ activeDashboards, onChange }) => {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string[]>([]);
  const modalRef = useRef<HTMLDivElement>(null);

  // Sync draft when opening
  useEffect(() => {
    if (open) setDraft([...activeDashboards]);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  }, [open]);

  const toggle = (uid: string) => {
    setDraft(prev =>
      prev.includes(uid)
        ? prev.filter(u => u !== uid)
        : [...prev, uid]
    );
  };

  const applyAndClose = () => {
    saveSelection(draft);
    onChange(draft);
    setOpen(false);
  };

  const resetDefaults = () => {
    const defaults = ['ext-svc-overview', 'ext-svc-detail', 'ext-svc-sla'];
    setDraft(defaults);
  };

  const selectAll = () => {
    setDraft(DASHBOARD_LIBRARY.map(d => d.uid));
  };

  const tierGroups = [1, 2, 3].map(tier => ({
    tier,
    label: tierLabel(tier),
    dashboards: DASHBOARD_LIBRARY.filter(d => d.tier === tier),
  }));

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setOpen(true)}
        className="btn-secondary text-sm font-medium flex items-center gap-2 px-4 py-2"
        title="Manage visible dashboards"
      >
        <Settings2 className="w-4 h-4" />
        Manage Dashboards
      </button>

      {/* Modal Overlay */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div
            ref={modalRef}
            className="bg-surface border border-surface-light rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-surface-light">
              <div>
                <h2 className="text-lg font-bold text-white">Dashboard Library</h2>
                <p className="text-text-muted text-sm mt-0.5">Select dashboards to display</p>
              </div>
              <button onClick={() => setOpen(false)} className="text-text-muted hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-4 max-h-[60vh] overflow-y-auto space-y-5">
              {tierGroups.map(({ tier, label, dashboards }) => (
                <div key={tier}>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
                    {label} Dashboards
                  </h3>
                  <div className="space-y-2">
                    {dashboards.map(d => (
                      <DashboardRow
                        key={d.uid}
                        entry={d}
                        active={draft.includes(d.uid)}
                        onToggle={() => toggle(d.uid)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-surface-light bg-surface-dark/30">
              <div className="flex items-center gap-2">
                <button
                  onClick={selectAll}
                  className="text-xs text-text-secondary hover:text-primary transition-colors"
                >
                  Select All
                </button>
                <span className="text-surface-light">|</span>
                <button
                  onClick={resetDefaults}
                  className="text-xs text-text-secondary hover:text-primary transition-colors flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  Defaults
                </button>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-text-muted">
                  {draft.length} of {DASHBOARD_LIBRARY.length} selected
                </span>
                <button
                  onClick={applyAndClose}
                  className="btn-primary text-sm font-medium px-5 py-2 flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

/* ── Row Item ── */

const DashboardRow: React.FC<{
  entry: DashboardEntry;
  active: boolean;
  onToggle: () => void;
}> = ({ entry, active, onToggle }) => (
  <button
    onClick={onToggle}
    className={`w-full flex items-start gap-3 p-3 rounded-lg border transition-all text-left ${
      active
        ? 'border-primary/40 bg-primary/5'
        : 'border-surface-light bg-transparent hover:bg-surface-light/30'
    }`}
  >
    {/* Checkbox */}
    <div
      className={`mt-0.5 w-5 h-5 rounded flex-shrink-0 flex items-center justify-center border transition-colors ${
        active
          ? 'bg-primary border-primary text-white'
          : 'border-surface-light bg-surface-dark/50'
      }`}
    >
      {active && <Check className="w-3.5 h-3.5" />}
    </div>

    {/* Info */}
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <span className="font-medium text-white text-sm">{entry.name}</span>
        <span className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded ${
          entry.tier === 1
            ? 'bg-primary/20 text-primary-light'
            : entry.tier === 2
              ? 'bg-secondary/20 text-secondary-light'
              : 'bg-warning/20 text-warning'
        }`}>
          {tierLabel(entry.tier)}
        </span>
      </div>
      <p className="text-text-muted text-xs mt-0.5 leading-relaxed">{entry.description}</p>
    </div>
  </button>
);
