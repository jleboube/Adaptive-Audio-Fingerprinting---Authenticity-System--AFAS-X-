"use client";

import { motion } from "framer-motion";
import { Upload, Fingerprint, Link2, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: Upload,
    title: "Upload Your Audio",
    description:
      "Upload any audio file - voice recordings, podcasts, music, or any content you want to protect.",
    color: "from-primary-500 to-primary-600",
  },
  {
    icon: Fingerprint,
    title: "6-Layer Fingerprinting",
    description:
      "Our system analyzes and embeds imperceptible fingerprints across spectral, temporal, and semantic dimensions.",
    color: "from-secondary-500 to-secondary-600",
  },
  {
    icon: Link2,
    title: "Blockchain Registration",
    description:
      "A cryptographic proof is permanently recorded on our blockchain, creating immutable provenance.",
    color: "from-accent-500 to-accent-600",
  },
  {
    icon: CheckCircle,
    title: "Verify Anytime",
    description:
      "Upload any audio to instantly verify its authenticity and detect modifications or AI-generated clones.",
    color: "from-primary-500 to-secondary-500",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 relative">
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
            How <span className="gradient-text">AFAS-X</span> Works
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A simple 4-step process to protect and verify your audio content
          </p>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Connection Line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 via-secondary-500 to-accent-500 transform -translate-y-1/2" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
                className="relative"
              >
                {/* Step Number */}
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 lg:relative lg:top-0 lg:left-0 lg:transform-none lg:flex lg:justify-center lg:mb-6">
                  <div
                    className={`w-16 h-16 rounded-full bg-gradient-to-br ${step.color} flex items-center justify-center shadow-lg relative z-10`}
                  >
                    <step.icon className="w-7 h-7 text-white" />
                  </div>
                </div>

                {/* Content */}
                <div className="pt-16 lg:pt-0 text-center">
                  <div className="text-sm font-medium text-muted-foreground mb-2">
                    Step {index + 1}
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
