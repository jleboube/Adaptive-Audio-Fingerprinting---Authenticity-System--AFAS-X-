"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Waves,
  Loader2,
  Mail,
  Lock,
  User,
  AlertCircle,
  AlertTriangle,
  Copy,
  Check,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Seed phrase modal state
  const [seedPhrase, setSeedPhrase] = useState<string | null>(null);
  const [showSeedModal, setShowSeedModal] = useState(false);
  const [seedCopied, setSeedCopied] = useState(false);
  const [seedAcknowledged, setSeedAcknowledged] = useState(false);

  const { register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter");
      return;
    }
    if (!/[a-z]/.test(password)) {
      setError("Password must contain at least one lowercase letter");
      return;
    }
    if (!/\d/.test(password)) {
      setError("Password must contain at least one digit");
      return;
    }

    setIsLoading(true);

    try {
      const result = await register(email, password, displayName || undefined);
      // Show seed phrase modal
      setSeedPhrase(result.seed_phrase);
      setShowSeedModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

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

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <Link href="/" className="flex items-center justify-center space-x-2 mb-8">
          <div className="relative">
            <Shield className="w-10 h-10 text-primary-400" />
            <Waves className="w-5 h-5 text-secondary-400 absolute -bottom-1 -right-1" />
          </div>
          <span className="text-2xl font-bold gradient-text">AFAS-X</span>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="text-center">Create Account</CardTitle>
            <p className="text-sm text-muted-foreground text-center">
              Protect your voice with AFAS-X fingerprinting
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && !showSeedModal && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="p-3 rounded-lg bg-red-500/10 border border-red-500/50 flex items-center gap-2"
                >
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <p className="text-sm text-red-400">{error}</p>
                </motion.div>
              )}

              <div className="space-y-2">
                <label htmlFor="displayName" className="text-sm font-medium">
                  Display Name <span className="text-muted-foreground">(optional)</span>
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="displayName"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Your name"
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 chars, uppercase, lowercase, digit"
                    required
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="text-sm font-medium">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    required
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="text-primary-400 hover:text-primary-300 font-medium"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Seed Phrase Modal */}
      <AnimatePresence>
        {showSeedModal && seedPhrase && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
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

                  {error && showSeedModal && (
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
