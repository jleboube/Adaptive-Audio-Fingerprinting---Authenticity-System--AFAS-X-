"use client";

import Link from "next/link";
import { Shield, Waves, Github, Twitter } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-border py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Shield className="w-6 h-6 text-primary-400" />
              <Waves className="w-3 h-3 text-secondary-400 absolute -bottom-0.5 -right-0.5" />
            </div>
            <span className="text-lg font-bold gradient-text">AFAS-X</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8 text-sm text-muted-foreground">
            <Link href="/dashboard" className="hover:text-foreground transition-colors">
              Dashboard
            </Link>
            <Link href="#features" className="hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#technology" className="hover:text-foreground transition-colors">
              Technology
            </Link>
          </div>

          {/* Social */}
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="p-2 rounded-lg hover:bg-muted transition-colors"
            >
              <Github className="w-5 h-5 text-muted-foreground hover:text-foreground" />
            </a>
            <a
              href="#"
              className="p-2 rounded-lg hover:bg-muted transition-colors"
            >
              <Twitter className="w-5 h-5 text-muted-foreground hover:text-foreground" />
            </a>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>
            &copy; {new Date().getFullYear()} AFAS-X. Audio Fingerprinting &
            Authenticity System.
          </p>
        </div>
      </div>
    </footer>
  );
}
