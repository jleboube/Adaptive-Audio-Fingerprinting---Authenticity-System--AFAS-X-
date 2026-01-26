"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileAudio,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { fileToBase64, formatDuration } from "@/lib/utils";

interface AudioUploaderProps {
  onUpload: (file: File, base64: string) => Promise<void>;
  title: string;
  description: string;
  acceptedFormats?: string[];
}

export default function AudioUploader({
  onUpload,
  title,
  description,
  acceptedFormats = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/flac", "audio/ogg"],
}: AudioUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"idle" | "processing" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const audioFile = acceptedFiles[0];
      if (!audioFile) return;

      setFile(audioFile);
      setStatus("processing");
      setIsProcessing(true);
      setError(null);
      setProgress(10);

      try {
        // Convert to base64
        setProgress(30);
        const base64 = await fileToBase64(audioFile);

        setProgress(60);
        await onUpload(audioFile, base64);

        setProgress(100);
        setStatus("success");
      } catch (err) {
        setStatus("error");
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsProcessing(false);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/*": acceptedFormats.map((f) => f.replace("audio/", ".")),
    },
    maxFiles: 1,
    disabled: isProcessing,
  });

  const reset = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setError(null);
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>

        <AnimatePresence mode="wait">
          {status === "idle" && (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
                  transition-all duration-200
                  ${
                    isDragActive
                      ? "border-primary-500 bg-primary-500/10"
                      : "border-border hover:border-primary-500/50 hover:bg-muted/50"
                  }
                `}
              >
                <input {...getInputProps()} />
                <Upload
                  className={`w-12 h-12 mx-auto mb-4 ${
                    isDragActive ? "text-primary-400" : "text-muted-foreground"
                  }`}
                />
                <p className="text-foreground font-medium mb-1">
                  {isDragActive ? "Drop your audio file here" : "Drag & drop audio file"}
                </p>
                <p className="text-sm text-muted-foreground">
                  or click to browse (WAV, MP3, FLAC, OGG)
                </p>
              </div>
            </motion.div>
          )}

          {(status === "processing" || status === "success" || status === "error") && file && (
            <motion.div
              key="file-info"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {/* File Info */}
              <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
                <div className="p-3 rounded-lg bg-primary-500/10">
                  <FileAudio className="w-6 h-6 text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                {status !== "processing" && (
                  <Button variant="ghost" size="icon" onClick={reset}>
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>

              {/* Progress */}
              {status === "processing" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Processing...</span>
                    <span className="text-foreground">{progress}%</span>
                  </div>
                  <Progress value={progress} />
                </div>
              )}

              {/* Status */}
              {status === "success" && (
                <div className="flex items-center gap-2 text-secondary-400">
                  <CheckCircle className="w-5 h-5" />
                  <span>Processing complete!</span>
                </div>
              )}

              {status === "error" && (
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Actions */}
              {(status === "success" || status === "error") && (
                <Button onClick={reset} variant="outline" className="w-full">
                  Upload Another File
                </Button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
