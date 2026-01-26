"use client";

import { motion } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Shield,
  Link2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { truncateHash } from "@/lib/utils";

interface LayerVerificationResult {
  layer_type: string;
  matches: boolean;
  confidence: number;
  details: string | null;
}

interface VerifyResultProps {
  result: {
    result: "AUTHENTIC" | "MODIFIED" | "UNKNOWN" | "FAILED";
    confidence_score: number;
    record_id: string | null;
    original_hash: string | null;
    layer_results: LayerVerificationResult[];
    blockchain_verified: boolean;
    provenance_chain: string[] | null;
    verified_at: string;
  };
}

const layerNames: Record<string, string> = {
  A: "Spectral",
  B: "Temporal",
  C: "Physiological",
  D: "Semantic",
  E: "Adversarial",
  F: "Meta",
};

const resultConfig = {
  AUTHENTIC: {
    icon: CheckCircle,
    color: "text-secondary-400",
    bgColor: "bg-secondary-500/10",
    borderColor: "border-secondary-500/50",
    title: "Authentic",
    description: "This audio matches the original fingerprinted recording.",
  },
  MODIFIED: {
    icon: AlertTriangle,
    color: "text-accent-400",
    bgColor: "bg-accent-500/10",
    borderColor: "border-accent-500/50",
    title: "Modified",
    description: "This audio has been modified from the original recording.",
  },
  UNKNOWN: {
    icon: HelpCircle,
    color: "text-muted-foreground",
    bgColor: "bg-muted/50",
    borderColor: "border-border",
    title: "Unknown",
    description: "No matching fingerprint found in our database.",
  },
  FAILED: {
    icon: XCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
    title: "Verification Failed",
    description: "Unable to verify this audio. Please try again.",
  },
};

export default function VerifyResult({ result }: VerifyResultProps) {
  const config = resultConfig[result.result];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Result Header */}
      <Card className={`${config.borderColor} ${config.bgColor}`}>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-full ${config.bgColor}`}>
              <Icon className={`w-8 h-8 ${config.color}`} />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold">{config.title}</h3>
              <p className="text-muted-foreground">{config.description}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold gradient-text">
                {(result.confidence_score * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Layer Results */}
      {result.layer_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary-400" />
              Layer Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {result.layer_results.map((layer, index) => (
              <motion.div
                key={layer.layer_type}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-4 p-3 rounded-lg bg-muted/30"
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    layer.matches
                      ? "bg-secondary-500/20 text-secondary-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {layer.matches ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <XCircle className="w-4 h-4" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      Layer {layer.layer_type}: {layerNames[layer.layer_type]}
                    </span>
                    <span
                      className={`text-sm ${
                        layer.matches ? "text-secondary-400" : "text-red-400"
                      }`}
                    >
                      {layer.matches ? "Match" : "Mismatch"}
                    </span>
                  </div>
                  <Progress
                    value={layer.confidence * 100}
                    className="h-1.5 mt-2"
                  />
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Blockchain & Provenance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5 text-accent-400" />
            Blockchain Verification
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            {result.blockchain_verified ? (
              <CheckCircle className="w-5 h-5 text-secondary-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <span>
              {result.blockchain_verified
                ? "Blockchain record verified"
                : "No blockchain record found"}
            </span>
          </div>

          {result.original_hash && (
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider">
                Original Hash
              </label>
              <code className="block text-sm bg-muted px-3 py-2 rounded-lg font-mono mt-1">
                {truncateHash(result.original_hash, 20)}
              </code>
            </div>
          )}

          {result.provenance_chain && result.provenance_chain.length > 0 && (
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider">
                Provenance Chain ({result.provenance_chain.length} blocks)
              </label>
              <div className="mt-2 space-y-1">
                {result.provenance_chain.slice(0, 3).map((hash, i) => (
                  <code
                    key={i}
                    className="block text-xs bg-muted px-2 py-1 rounded font-mono text-muted-foreground"
                  >
                    {truncateHash(hash, 16)}
                  </code>
                ))}
                {result.provenance_chain.length > 3 && (
                  <span className="text-xs text-muted-foreground">
                    ... and {result.provenance_chain.length - 3} more blocks
                  </span>
                )}
              </div>
            </div>
          )}

          <p className="text-sm text-muted-foreground">
            Verified at: {new Date(result.verified_at).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
