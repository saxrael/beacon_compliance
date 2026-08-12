"use client";

import { API_BASE_URL } from "@/config";
import { Download, FileCheck, Copy, Check } from "lucide-react";

interface DeliverableItem {
  deliverable_id: string;
  type: string;
  charity_number: string;
  status: string;
  content_hash?: string;
}

interface DeliverableGridProps {
  deliverables: DeliverableItem[];
  onOpenSignoff: (hash: string) => void;
  signatures: Record<string, string>;
}

export const DeliverableDownloadGrid: React.FC<DeliverableGridProps> = ({
  deliverables,
  onOpenSignoff,
  signatures,
}) => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const copyHash = (hash?: string) => {
    if (!hash) return;
    navigator.clipboard.writeText(hash);
    setCopiedId(hash);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const titles: Record<string, string> = {
    OAR: "Deliverable 1: OSCR Online Annual Return (OAR) Sheet",
    TAR: "Deliverable 2: Trustees' Annual Report (TAR)",
    RP: "Deliverable 3: Annual Receipts & Payments Accounts",
    IE: "Deliverable 4: Independent Examiner (IE) Review Pack",
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
        <FileCheck className="h-5 w-5 text-amber-400" />
        Compiled OSCR Deliverables
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {deliverables.map((item) => {
          const title = titles[item.type] || item.type;
          const hash = item.content_hash || "";
          const signed = Boolean(signatures[hash]);

          return (
            <div key={item.deliverable_id} className="glass-card rounded-xl p-5 border border-slate-700/60 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold">
                    {item.type} Package
                  </span>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded ${signed ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-400"}`}>
                    {signed ? "Trustee Signed" : "Pending Sign-off"}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-100 mt-2">{title}</h3>
                <div className="mt-3 flex items-center justify-between bg-slate-900/80 p-2 rounded border border-slate-800 text-[11px] font-mono text-slate-400">
                  <span className="truncate max-w-[200px]">{hash ? `${hash.substring(0, 16)}...` : "Calculating hash..."}</span>
                  <button onClick={() => copyHash(hash)} className="text-slate-400 hover:text-amber-400 p-1">
                    {copiedId === hash ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
                {!signed ? (
                  <button
                    onClick={() => onOpenSignoff(hash)}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 text-xs font-bold py-2 rounded-lg transition-colors"
                  >
                    Sign Off Deliverable
                  </button>
                ) : (
                  <a
                    href={`${API_BASE_URL}/api/deliverables/run_001`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full amber-gradient text-slate-950 text-xs font-bold py-2 rounded-lg transition-opacity hover:opacity-90 flex items-center justify-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download Package
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
