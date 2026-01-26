"use client";

import { motion } from "framer-motion";
import {
  Waves,
  Clock,
  Heart,
  MessageSquare,
  Shield,
  Layers,
  CheckCircle,
  Lock,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    icon: Waves,
    title: "Spectral Analysis",
    description:
      "Layer A: Psychoacoustic masking embeds imperceptible frequency perturbations unique to your audio.",
    color: "text-primary-400",
    bgColor: "bg-primary-500/10",
  },
  {
    icon: Clock,
    title: "Temporal Fingerprinting",
    description:
      "Layer B: Phase coherence and micro-timing analysis creates a temporal signature that's impossible to replicate.",
    color: "text-primary-300",
    bgColor: "bg-primary-400/10",
  },
  {
    icon: Heart,
    title: "Physiological Markers",
    description:
      "Layer C: Jitter, shimmer, and harmonic analysis detect natural voice characteristics vs. AI synthesis.",
    color: "text-secondary-400",
    bgColor: "bg-secondary-500/10",
  },
  {
    icon: MessageSquare,
    title: "Semantic Features",
    description:
      "Layer D: Prosody, emphasis patterns, and pause structures capture the unique way you speak.",
    color: "text-secondary-300",
    bgColor: "bg-secondary-400/10",
  },
  {
    icon: Shield,
    title: "Adversarial Protection",
    description:
      "Layer E: Anti-cloning perturbations designed to disrupt voice cloning and deepfake systems.",
    color: "text-accent-400",
    bgColor: "bg-accent-500/10",
  },
  {
    icon: Layers,
    title: "Cross-Layer Validation",
    description:
      "Layer F: Meta-analysis ensures consistency across all layers, detecting sophisticated tampering.",
    color: "text-accent-300",
    bgColor: "bg-accent-400/10",
  },
];

const benefits = [
  "Immutable blockchain provenance",
  "Real-time verification",
  "API integration ready",
  "Enterprise-grade security",
];

export default function Features() {
  return (
    <section id="features" className="py-24 relative">
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
            <span className="gradient-text">6-Layer</span> Protection System
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Each layer provides unique protection that works together to create
            an unbreakable chain of authenticity verification.
          </p>
        </motion.div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="h-full hover:border-primary-500/50 transition-colors group">
                <CardContent className="p-6">
                  <div
                    className={`inline-flex p-3 rounded-xl ${feature.bgColor} mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <feature.icon className={`w-6 h-6 ${feature.color}`} />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Benefits Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="glass rounded-2xl p-8"
        >
          <div className="flex flex-wrap justify-center gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-secondary-400" />
                <span className="text-foreground">{benefit}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
