"use client";

import dynamic from "next/dynamic";
import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import Technology from "@/components/landing/Technology";
import CTA from "@/components/landing/CTA";
import Footer from "@/components/landing/Footer";

// Dynamic import for Three.js component to avoid SSR issues
const WaveAnimation = dynamic(() => import("@/components/landing/WaveAnimation"), {
  ssr: false,
  loading: () => (
    <div className="absolute inset-0 -z-10 bg-gradient-to-b from-background via-background to-muted" />
  ),
});

export default function Home() {
  return (
    <main className="relative min-h-screen bg-background overflow-hidden">
      {/* Animated Background */}
      <WaveAnimation />

      {/* Navigation */}
      <Navbar />

      {/* Hero Section */}
      <Hero />

      {/* Features Section */}
      <Features />

      {/* How It Works */}
      <HowItWorks />

      {/* Technology */}
      <Technology />

      {/* Call to Action */}
      <CTA />

      {/* Footer */}
      <Footer />
    </main>
  );
}
