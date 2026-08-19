import { useState, useEffect, useCallback } from "react";
import { API_BASE_URL } from "@/config";

export interface PipelineResult {
  run_id: string;
  income_threshold_breach: boolean;
  receipts_payments: {
    gross_receipts_decimal?: string;
    gross_payments_decimal?: string;
    net_movement_decimal?: string;
  };
  statement_of_balances: {
    reconciled?: boolean;
  };
  tar_draft_fields?: {
    governance_description?: string;
    purposes_activities_narrative?: string;
    achievements_connective_narrative?: string;
    principal_risks_narrative?: string;
  };
  deliverables?: Array<{
    deliverable_id: string;
    type: string;
    charity_number: string;
    status: string;
    content_hash?: string;
  }>;
}

export function useComplianceOS() {
  const [trusteeRole, setTrusteeRole] = useState("chair");
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeSignoffHash, setActiveSignoffHash] = useState<string | null>(null);
  const [signatures, setSignatures] = useState<Record<string, string>>({});

  const runCompliancePipeline = useCallback(async () => {
    setLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null;
      const res = await fetch(`${API_BASE_URL}/api/pipeline/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ run_id: "run_001", opening_balance_pence: 500000, closing_balance_pence: 2000000 }),
      });
      if (res.ok) {
        const data = (await res.json()) as PipelineResult;
        setPipelineResult(data);
      }
    } catch {
      console.error("Failed to generate annual charity compliance accounts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runCompliancePipeline();
  }, [runCompliancePipeline]);

  const handleSignoffSuccess = (hash: string, signatureHex: string) => {
    setSignatures((prev) => ({ ...prev, [hash]: signatureHex }));
    setActiveSignoffHash(null);
  };

  return {
    trusteeRole,
    setTrusteeRole,
    pipelineResult,
    loading,
    activeSignoffHash,
    setActiveSignoffHash,
    signatures,
    runCompliancePipeline,
    handleSignoffSuccess,
  };
}
