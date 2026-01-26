"use client";

import { motion } from "framer-motion";
import { Database, Cpu, Lock, Zap } from "lucide-react";

const techStack = [
  {
    icon: Cpu,
    title: "Advanced DSP",
    description: "Librosa-powered spectral analysis with FFT, MFCC, and psychoacoustic modeling",
    items: ["Mel Spectrograms", "Phase Analysis", "Onset Detection"],
  },
  {
    icon: Database,
    title: "Custom Blockchain",
    description: "PostgreSQL-backed chain with SHA-256 hashing and Ed25519 signatures",
    items: ["Immutable Records", "Chain Verification", "Provenance Tracking"],
  },
  {
    icon: Lock,
    title: "Cryptographic Security",
    description: "Military-grade encryption and digital signatures for authenticity",
    items: ["Ed25519 Signatures", "SHA-256 Hashing", "Secure Key Management"],
  },
  {
    icon: Zap,
    title: "Real-time Processing",
    description: "Async architecture with Celery workers for instant fingerprinting",
    items: ["FastAPI Backend", "Redis Caching", "Background Workers"],
  },
];

export default function Technology() {
  return (
    <section id="technology" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            Powered by <span className="gradient-text">Cutting-Edge</span> Tech
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Built on proven technologies for reliability, security, and performance
          </p>
        </motion.div>

        {/* Tech Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {techStack.map((tech, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="glass rounded-2xl p-8 hover:border-primary-500/30 transition-all group"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500/20 to-secondary-500/20 group-hover:scale-110 transition-transform">
                  <tech.icon className="w-8 h-8 text-primary-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-2">{tech.title}</h3>
                  <p className="text-muted-foreground mb-4">{tech.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {tech.items.map((item, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 text-sm rounded-full bg-muted text-muted-foreground"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* API Preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mt-16"
        >
          <div className="glass rounded-2xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-muted/50 border-b border-border">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="ml-4 text-sm text-muted-foreground font-mono">
                API Example
              </span>
            </div>
            <pre className="p-6 overflow-x-auto">
              <code className="text-sm font-mono">
                <span className="text-secondary-400">POST</span>{" "}
                <span className="text-foreground">/fingerprint</span>
                {"\n"}
                <span className="text-muted-foreground">{"{"}</span>
                {"\n"}
                <span className="text-primary-400">  "audio_base64"</span>
                <span className="text-muted-foreground">:</span>{" "}
                <span className="text-accent-400">"UklGRi..."</span>
                <span className="text-muted-foreground">,</span>
                {"\n"}
                <span className="text-primary-400">  "creator_id"</span>
                <span className="text-muted-foreground">:</span>{" "}
                <span className="text-accent-400">"user_123"</span>
                {"\n"}
                <span className="text-muted-foreground">{"}"}</span>
              </code>
            </pre>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
