"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Waves,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Copy,
  Check,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function GoogleCallbackPage() {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Seed phrase modal state (for new users)
  const [seedPhrase, setSeedPhrase] = useState<string | null>(null);
  const [showSeedModal, setShowSeedModal] = useState(false);
  const [seedCopied, setSeedCopied] = useState(false);
  const [seedAcknowledged, setSeedAcknowledged] = useState(false);

  const { handleGoogleCallback } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError(`Google authentication failed: ${errorParam}`);
      setIsLoading(false);
      return;
    }

    if (!code) {
      setError("No authorization code received from Google");
      setIsLoading(false);
      return;
    }

    // Exchange code for tokens
    handleGoogleCallback(code)
      .then((response) => {
        if (response.is_new_user && response.seed_phrase) {
          // New user - show seed phrase modal
          setSeedPhrase(response.seed_phrase);
          setShowSeedModal(true);
          setIsLoading(false);
        } else {
          // Existing user - redirect to dashboard
          router.push("/dashboard");
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Authentication failed");
        setIsLoading(false);
      });
  }, [searchParams, handleGoogleCallback, router]);

  const handleCopySeed = async () => {
    if (!seedPhrase) return;
    await navigator.clipboard.writeText(seedPhrase);
    setSeedCopied(true);
    setTimeout(() => setSeedCopied(false), 2000);
  };

  const handleContinue = () => {
    if (!seedAcknowledged) {
      setError("Please confirm you have saved your seed phrase");
      return;
    }
    setShowSeedModal(false);
    router.push("/dashboard");
  };

  // Loading state
  if (isLoading && !showSeedModal) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="relative mb-6 inline-flex">
            <Shield className="w-16 h-16 text-primary-400" />
            <Waves className="w-8 h-8 text-secondary-400 absolute -bottom-2 -right-2" />
          </div>
          <h1 className="text-xl font-semibold mb-2">Authenticating with Google</h1>
          <p className="text-muted-foreground mb-4">Please wait...</p>
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-400" />
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error && !showSeedModal) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-red-400">
                Authentication Failed
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/50 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
              <Button
                className="w-full"
                onClick={() => router.push("/login")}
              >
                Back to Login
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  // Seed phrase modal for new users
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <AnimatePresence>
        {showSeedModal && seedPhrase && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full max-w-lg"
          >
            <Card className="border-amber-500/50">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <Key className="w-6 h-6 text-amber-400" />
                  </div>
                  <div>
                    <CardTitle>Your Recovery Seed Phrase</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      This is the ONLY time you will see this!
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Welcome message */}
                <div className="p-4 rounded-lg bg-primary-500/10 border border-primary-500/50">
                  <p className="text-sm text-primary-400">
                    Welcome to AFAS-X! Your account has been created with Google.
                  </p>
                </div>

                {/* Warning */}
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/50">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div className="space-y-2 text-sm">
                      <p className="font-semibold text-amber-400">
                        CRITICAL: Save this phrase securely!
                      </p>
                      <ul className="list-disc list-inside text-muted-foreground space-y-1">
                        <li>This phrase proves ownership of your voice fingerprints</li>
                        <li>It will NEVER be shown again and CANNOT be recovered</li>
                        <li>If lost, you lose the ability to prove ownership</li>
                        <li>Store it offline in a secure location</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Seed Phrase */}
                <div className="p-4 rounded-lg bg-muted border border-border font-mono text-sm leading-relaxed">
                  {seedPhrase}
                </div>

                {/* Copy Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleCopySeed}
                >
                  {seedCopied ? (
                    <>
                      <Check className="w-4 h-4 mr-2 text-secondary-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" />
                      Copy to Clipboard
                    </>
                  )}
                </Button>

                {/* Acknowledgment Checkbox */}
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={seedAcknowledged}
                    onChange={(e) => setSeedAcknowledged(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-border bg-muted"
                  />
                  <span className="text-sm text-muted-foreground">
                    I understand that this seed phrase is the ONLY way to prove ownership
                    of my voice fingerprints, and I have saved it securely.
                  </span>
                </label>

                {error && (
                  <p className="text-sm text-red-400 text-center">{error}</p>
                )}

                {/* Continue Button */}
                <Button
                  className="w-full"
                  onClick={handleContinue}
                  disabled={!seedAcknowledged}
                >
                  Continue to Dashboard
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
