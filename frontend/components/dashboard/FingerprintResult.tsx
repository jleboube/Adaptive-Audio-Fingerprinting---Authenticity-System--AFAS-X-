"use client";

import { motion } from "framer-motion";
import {
  Download,
  Copy,
  CheckCircle,
  Layers,
  Link2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { truncateHash } from "@/lib/utils";

interface LayerResult {
  layer_type: string;
  layer_hash: string;
  confidence_score: number;
}

interface FingerprintResultProps {
  result: {
    record_id: string;
    original_hash: string;
    fingerprinted_hash: string;
    fingerprinted_audio_base64: string;
    layers: LayerResult[];
    blockchain_hash: string;
    ethereum_tx_hash: string | null;
    version: string;
    created_at: string;
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

const layerColors: Record<string, string> = {
  A: "from-primary-500 to-primary-600",
  B: "from-primary-400 to-primary-500",
  C: "from-secondary-500 to-secondary-600",
  D: "from-secondary-400 to-secondary-500",
  E: "from-accent-500 to-accent-600",
  F: "from-accent-400 to-accent-500",
};

export default function FingerprintResult({ result }: FingerprintResultProps) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = async (text: string, label: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  const downloadAudio = () => {
    const link = document.createElement("a");
    link.href = `data:audio/wav;base64,${result.fingerprinted_audio_base64}`;
    link.download = `fingerprinted-${result.record_id.slice(0, 8)}.wav`;
    link.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Success Header */}
      <Card className="border-secondary-500/50 bg-secondary-500/5">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-secondary-500/20">
              <CheckCircle className="w-8 h-8 text-secondary-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Fingerprint Created!</h3>
              <p className="text-muted-foreground">
                Your audio has been fingerprinted and registered on the blockchain.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Layer Results */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary-400" />
            Fingerprint Layers
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {result.layers.map((layer, index) => (
            <motion.div
              key={layer.layer_type}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-lg bg-muted/50"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg bg-gradient-to-br ${
                      layerColors[layer.layer_type]
                    } flex items-center justify-center text-white font-bold text-sm`}
                  >
                    {layer.layer_type}
                  </div>
                  <div>
                    <span className="font-medium">
                      Layer {layer.layer_type}: {layerNames[layer.layer_type]}
                    </span>
                    <p className="text-xs text-muted-foreground font-mono">
                      {truncateHash(layer.layer_hash, 12)}
                    </p>
                  </div>
                </div>
                <span className="text-sm font-medium">
                  {(layer.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={layer.confidence_score * 100} />
            </motion.div>
          ))}
        </CardContent>
      </Card>

      {/* Hashes & Blockchain */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Link2 className="w-4 h-4 text-primary-400" />
              Hashes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider">
                Original Hash
              </label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 text-sm bg-muted px-3 py-2 rounded-lg font-mono truncate">
                  {truncateHash(result.original_hash, 16)}
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => copyToClipboard(result.original_hash, "original")}
                >
                  {copied === "original" ? (
                    <CheckCircle className="w-4 h-4 text-secondary-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider">
                Fingerprinted Hash
              </label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 text-sm bg-muted px-3 py-2 rounded-lg font-mono truncate">
                  {truncateHash(result.fingerprinted_hash, 16)}
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    copyToClipboard(result.fingerprinted_hash, "fingerprinted")
                  }
                >
                  {copied === "fingerprinted" ? (
                    <CheckCircle className="w-4 h-4 text-secondary-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="w-4 h-4 text-secondary-400" />
              Blockchain Record
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider">
                Local Block Hash
              </label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 text-sm bg-muted px-3 py-2 rounded-lg font-mono truncate">
                  {truncateHash(result.blockchain_hash, 16)}
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => copyToClipboard(result.blockchain_hash, "block")}
                >
                  {copied === "block" ? (
                    <CheckCircle className="w-4 h-4 text-secondary-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            {result.ethereum_tx_hash && (
              <div>
                <label className="text-xs text-muted-foreground uppercase tracking-wider">
                  Ethereum TX (Sepolia)
                </label>
                <div className="flex items-center gap-2 mt-1">
                  <code className="flex-1 text-sm bg-muted px-3 py-2 rounded-lg font-mono truncate">
                    {truncateHash(result.ethereum_tx_hash, 12)}
                  </code>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => copyToClipboard(result.ethereum_tx_hash!, "eth")}
                  >
                    {copied === "eth" ? (
                      <CheckCircle className="w-4 h-4 text-secondary-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    asChild
                  >
                    <a
                      href={`https://sepolia.etherscan.io/tx/${result.ethereum_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                </div>
              </div>
            )}
            <div className="text-sm text-muted-foreground">
              <p>Version: {result.version}</p>
              <p>Created: {new Date(result.created_at).toLocaleString()}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Download */}
      <Button onClick={downloadAudio} className="w-full" size="lg">
        <Download className="w-4 h-4 mr-2" />
        Download Fingerprinted Audio
      </Button>
    </motion.div>
  );
}
