"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Fingerprint,
  Shield,
  Search,
  Layers,
  Activity,
  Database,
  Loader2,
  Wallet,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import AudioUploader from "@/components/dashboard/AudioUploader";
import FingerprintResult from "@/components/dashboard/FingerprintResult";
import VerifyResult from "@/components/dashboard/VerifyResult";
import { apiRequest, authenticatedApiRequest } from "@/lib/utils";

type Tab = "fingerprint" | "verify" | "provenance";

interface SystemStats {
  api_status: string;
  database_status: string;
  redis_status: string;
  blockchain_status: string;
  blockchain_blocks: number;
  blockchain_synced: boolean;
  ethereum_connected: boolean;
  ethereum_network: string | null;
  ethereum_wallet: string | null;
  ethereum_balance: number | null;
  total_fingerprints: number;
  total_verifications: number;
  active_layers: number;
  timestamp: string;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("fingerprint");
  const [fingerprintResult, setFingerprintResult] = useState<any>(null);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [provenanceHash, setProvenanceHash] = useState("");
  const [provenanceResult, setProvenanceResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Fetch real stats from API
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setStatsLoading(true);
        setStatsError(null);
        const data = await apiRequest<SystemStats>("/stats");
        setStats(data);
      } catch (err) {
        setStatsError("Failed to fetch system stats");
        console.error("Stats fetch error:", err);
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFingerprint = async (file: File, base64: string) => {
    const result = await authenticatedApiRequest("/fingerprint", {
      method: "POST",
      body: JSON.stringify({
        audio_base64: base64,
        file_name: file.name,
      }),
    });
    setFingerprintResult(result);
  };

  const handleVerify = async (file: File, base64: string) => {
    const result = await apiRequest("/verify", {
      method: "POST",
      body: JSON.stringify({
        audio_base64: base64,
      }),
    });
    setVerifyResult(result);
  };

  const handleProvenanceLookup = async () => {
    if (!provenanceHash.trim()) return;
    setLoading(true);
    try {
      const result = await apiRequest(`/provenance/${provenanceHash}`);
      setProvenanceResult(result);
    } catch (err) {
      setProvenanceResult({ found: false, error: "Lookup failed" });
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    {
      id: "fingerprint" as Tab,
      label: "Fingerprint",
      icon: Fingerprint,
      description: "Embed fingerprints into audio",
    },
    {
      id: "verify" as Tab,
      label: "Verify",
      icon: Shield,
      description: "Check audio authenticity",
    },
    {
      id: "provenance" as Tab,
      label: "Provenance",
      icon: Search,
      description: "Lookup blockchain records",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Fingerprint, verify, and track your audio files
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {statsLoading ? (
          <Card className="col-span-full">
            <CardContent className="p-4 flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              <span className="text-muted-foreground">Loading system stats...</span>
            </CardContent>
          </Card>
        ) : statsError ? (
          <Card className="col-span-full border-red-500/50">
            <CardContent className="p-4 text-center text-red-400">
              {statsError} - Backend may be offline
            </CardContent>
          </Card>
        ) : stats ? (
          <>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-2 rounded-lg bg-muted">
                  <Layers className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{stats.active_layers} Layers</p>
                  <p className="font-semibold">Active</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-2 rounded-lg bg-muted">
                  <Activity className={`w-5 h-5 ${stats.api_status === "online" ? "text-secondary-400" : "text-red-400"}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">API Status</p>
                  <p className="font-semibold capitalize">{stats.api_status}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-2 rounded-lg bg-muted">
                  <Database className={`w-5 h-5 ${stats.blockchain_synced ? "text-accent-400" : "text-red-400"}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Local Chain</p>
                  <p className="font-semibold">{stats.blockchain_synced ? "Synced" : "Offline"} ({stats.blockchain_blocks} blocks)</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-2 rounded-lg bg-muted">
                  <Wallet className={`w-5 h-5 ${stats.ethereum_connected ? "text-secondary-400" : "text-muted-foreground"}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Ethereum</p>
                  <p className="font-semibold">
                    {stats.ethereum_connected
                      ? `${stats.ethereum_network} (${stats.ethereum_balance?.toFixed(4) || 0} ETH)`
                      : "Not Connected"}
                  </p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="p-2 rounded-lg bg-muted">
                  <Fingerprint className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Fingerprints</p>
                  <p className="font-semibold">{stats.total_fingerprints}</p>
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 p-1 bg-muted rounded-xl">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setFingerprintResult(null);
              setVerifyResult(null);
              setProvenanceResult(null);
            }}
            className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
              activeTab === tab.id
                ? "bg-background text-foreground shadow-lg"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Fingerprint Tab */}
        {activeTab === "fingerprint" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AudioUploader
              title="Create Fingerprint"
              description="Upload audio to embed a unique fingerprint and register on blockchain"
              onUpload={handleFingerprint}
            />
            {fingerprintResult && (
              <div className="lg:col-span-2">
                <FingerprintResult result={fingerprintResult} />
              </div>
            )}
          </div>
        )}

        {/* Verify Tab */}
        {activeTab === "verify" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AudioUploader
              title="Verify Authenticity"
              description="Upload audio to check if it matches a fingerprinted original"
              onUpload={handleVerify}
            />
            {verifyResult && (
              <div className="lg:col-span-2">
                <VerifyResult result={verifyResult} />
              </div>
            )}
          </div>
        )}

        {/* Provenance Tab */}
        {activeTab === "provenance" && (
          <Card>
            <CardHeader>
              <CardTitle>Provenance Lookup</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={provenanceHash}
                  onChange={(e) => setProvenanceHash(e.target.value)}
                  placeholder="Enter audio hash..."
                  className="flex-1 px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none font-mono text-sm"
                />
                <Button onClick={handleProvenanceLookup} disabled={loading}>
                  {loading ? "Looking up..." : "Lookup"}
                </Button>
              </div>

              {provenanceResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6"
                >
                  {provenanceResult.found ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-secondary-500/10 border border-secondary-500/50">
                        <h4 className="font-semibold text-secondary-400 mb-2">
                          Record Found
                        </h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Record ID:</span>
                            <p className="font-mono">{provenanceResult.audio_info?.record_id}</p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Created:</span>
                            <p>
                              {new Date(
                                provenanceResult.audio_info?.created_at
                              ).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Creator:</span>
                            <p>{provenanceResult.audio_info?.creator_id || "N/A"}</p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Chain Valid:</span>
                            <p className={provenanceResult.chain_valid ? "text-secondary-400" : "text-red-400"}>
                              {provenanceResult.chain_valid ? "Yes" : "No"}
                            </p>
                          </div>
                        </div>
                      </div>

                      {provenanceResult.layers && (
                        <div>
                          <h4 className="font-semibold mb-2">Fingerprint Layers</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {provenanceResult.layers.map((layer: any) => (
                              <div
                                key={layer.layer_type}
                                className="p-3 rounded-lg bg-muted text-sm"
                              >
                                <span className="font-medium">Layer {layer.layer_type}</span>
                                <p className="text-muted-foreground text-xs font-mono truncate">
                                  {layer.layer_hash}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg bg-muted text-center">
                      <p className="text-muted-foreground">
                        No record found for this hash
                      </p>
                    </div>
                  )}
                </motion.div>
              )}
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
