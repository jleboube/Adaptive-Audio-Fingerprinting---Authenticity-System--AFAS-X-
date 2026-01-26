"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Key,
  Plus,
  Trash2,
  Loader2,
  Copy,
  Check,
  AlertTriangle,
  Clock,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { authenticatedApiRequest } from "@/lib/utils";

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

interface NewKeyResponse {
  id: string;
  name: string;
  key: string;
  key_prefix: string;
  scopes: string[];
  expires_at: string | null;
  created_at: string;
}

export default function APIKeysPage() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyExpires, setNewKeyExpires] = useState<string>("");
  const [isCreating, setIsCreating] = useState(false);

  // New key display state
  const [newKeyResult, setNewKeyResult] = useState<NewKeyResponse | null>(null);
  const [keyCopied, setKeyCopied] = useState(false);

  // Delete state
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await authenticatedApiRequest<{ keys: APIKey[]; total: number }>(
        "/auth/api-keys"
      );
      setKeys(response.keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch API keys");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    setError(null);

    try {
      const body: { name: string; expires_in_days?: number; scopes: string[] } = {
        name: newKeyName,
        scopes: ["fingerprint:create", "verify:read"],
      };

      if (newKeyExpires) {
        body.expires_in_days = parseInt(newKeyExpires, 10);
      }

      const result = await authenticatedApiRequest<NewKeyResponse>(
        "/auth/api-keys",
        {
          method: "POST",
          body: JSON.stringify(body),
        }
      );

      setNewKeyResult(result);
      setNewKeyName("");
      setNewKeyExpires("");
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key");
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteKeyId) return;
    setIsDeleting(true);

    try {
      await authenticatedApiRequest(`/auth/api-keys/${deleteKeyId}`, {
        method: "DELETE",
      });
      setDeleteKeyId(null);
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete API key");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCopyKey = async () => {
    if (!newKeyResult?.key) return;
    await navigator.clipboard.writeText(newKeyResult.key);
    setKeyCopied(true);
    setTimeout(() => setKeyCopied(false), 2000);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-muted-foreground">
            Manage API keys for programmatic access
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Key
        </Button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/50 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* API Keys List */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              Your API Keys
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : keys.length === 0 ? (
              <div className="text-center py-8">
                <Key className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No API keys yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Create one to start using the AFAS-X API
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {keys.map((key) => (
                  <div
                    key={key.id}
                    className={`p-4 rounded-lg border ${
                      key.is_active
                        ? "border-border bg-muted/50"
                        : "border-red-500/30 bg-red-500/5"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{key.name}</h3>
                          {!key.is_active && (
                            <span className="px-2 py-0.5 text-xs rounded bg-red-500/20 text-red-400">
                              Revoked
                            </span>
                          )}
                        </div>
                        <p className="font-mono text-sm text-muted-foreground mt-1">
                          {key.key_prefix}...
                        </p>
                        <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Created {formatDate(key.created_at)}
                          </span>
                          {key.last_used_at && (
                            <span>Last used {formatDate(key.last_used_at)}</span>
                          )}
                          {key.expires_at && (
                            <span className="text-amber-400">
                              Expires {formatDate(key.expires_at)}
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {key.scopes.map((scope) => (
                            <span
                              key={scope}
                              className="px-2 py-0.5 text-xs rounded bg-primary-500/20 text-primary-400"
                            >
                              {scope}
                            </span>
                          ))}
                        </div>
                      </div>
                      {key.is_active && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-400 hover:text-red-300 hover:border-red-500/50"
                          onClick={() => setDeleteKeyId(key.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Usage Info */}
      <Card className="border-primary-500/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary-500/10">
              <Shield className="w-4 h-4 text-primary-400" />
            </div>
            <div>
              <p className="font-medium text-primary-400">Using API Keys</p>
              <p className="text-sm text-muted-foreground mt-1">
                Include your API key in requests using the{" "}
                <code className="px-1 py-0.5 rounded bg-muted font-mono text-xs">
                  X-API-Key
                </code>{" "}
                header. API keys provide the same access as your account for
                fingerprinting and verification operations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
            onClick={() => !isCreating && setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Create API Key</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="keyName" className="text-sm font-medium">
                        Key Name
                      </label>
                      <input
                        id="keyName"
                        type="text"
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        placeholder="e.g., Production Server"
                        required
                        className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none"
                      />
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="keyExpires" className="text-sm font-medium">
                        Expires In (Days){" "}
                        <span className="text-muted-foreground">(optional)</span>
                      </label>
                      <input
                        id="keyExpires"
                        type="number"
                        min="1"
                        max="365"
                        value={newKeyExpires}
                        onChange={(e) => setNewKeyExpires(e.target.value)}
                        placeholder="Leave empty for no expiration"
                        className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary-500 focus:outline-none"
                      />
                    </div>

                    <div className="flex gap-2 justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setShowCreateModal(false)}
                        disabled={isCreating}
                      >
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isCreating}>
                        {isCreating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          "Create Key"
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* New Key Result Modal */}
      <AnimatePresence>
        {newKeyResult && (
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
              <Card className="border-secondary-500/50">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-secondary-500/20">
                      <Key className="w-6 h-6 text-secondary-400" />
                    </div>
                    <div>
                      <CardTitle>API Key Created</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        Save this key now - it won&apos;t be shown again!
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/50">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-amber-400">
                        This is the only time you will see the full API key.
                        Copy it now and store it securely.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">API Key</label>
                    <div className="p-3 rounded-lg bg-muted border border-border font-mono text-sm break-all">
                      {newKeyResult.key}
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={handleCopyKey}
                  >
                    {keyCopied ? (
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

                  <Button
                    className="w-full"
                    onClick={() => {
                      setNewKeyResult(null);
                      setShowCreateModal(false);
                    }}
                  >
                    Done
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteKeyId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
            onClick={() => !isDeleting && setDeleteKeyId(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="border-red-500/50">
                <CardHeader>
                  <CardTitle className="text-red-400">Revoke API Key?</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    This action cannot be undone. Any applications using this
                    API key will no longer be able to authenticate.
                  </p>

                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      onClick={() => setDeleteKeyId(null)}
                      disabled={isDeleting}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="outline"
                      className="text-red-400 hover:text-red-300 hover:border-red-500/50"
                      onClick={handleDelete}
                      disabled={isDeleting}
                    >
                      {isDeleting ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Revoking...
                        </>
                      ) : (
                        "Revoke Key"
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
