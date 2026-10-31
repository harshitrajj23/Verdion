"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

const sentences = [
  "Autonomous multi-agent intelligence tailored for European AI Act and GDPR compliance.",
  "Empirical prediction markets aggregating probabilistic consensus across legal evaluators.",
  "Cryptographically verifiable audit trails anchored with on-chain commit-reveal scoring.",
  "Transforming complex regulatory uncertainty into grounded, evidence-backed decisions."
];

export default function LandingPage() {
  const [sentenceIndex, setSentenceIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentSentence = sentences[sentenceIndex];
    let timer: NodeJS.Timeout;

    if (!isDeleting) {
      if (displayedText.length < currentSentence.length) {
        timer = setTimeout(() => {
          setDisplayedText(currentSentence.slice(0, displayedText.length + 1));
        }, 45);
      } else {
        // Pause after sentence completes typing
        timer = setTimeout(() => {
          setIsDeleting(true);
        }, 2600);
      }
    } else {
      if (displayedText.length > 0) {
        timer = setTimeout(() => {
          setDisplayedText(currentSentence.slice(0, displayedText.length - 1));
        }, 22);
      } else {
        // Move to next sentence
        setIsDeleting(false);
        setSentenceIndex((prev) => (prev + 1) % sentences.length);
      }
    }

    return () => clearTimeout(timer);
  }, [displayedText, isDeleting, sentenceIndex]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center text-center px-6 overflow-hidden bg-black select-none">
      {/* Background Animated WebP */}
      <img
        src="/pinkBg.webp"
        alt="Veridion Background"
        className="absolute inset-0 w-full h-full object-cover pointer-events-none brightness-105 contrast-105"
      />

      {/* Subtle Luminous Tint & Contrast Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/30 pointer-events-none" />

      {/* Hero Content */}
      <div className="relative z-10 flex flex-col items-center max-w-3xl space-y-7 animate-fade-in">
        {/* Subtle Category Pill */}
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-mono font-medium tracking-widest uppercase text-white/80 bg-white/10 border border-white/20 backdrop-blur-md">
          Decentralized Protocol
        </span>

        {/* Heading Veridion in White Aesthetic Editorial Font */}
        <h1 className="font-display text-6xl sm:text-8xl md:text-9xl font-normal tracking-tight text-white drop-shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          Veridion
        </h1>

        {/* Typewriter Effect (3-4 sentences about project) */}
        <div className="h-24 sm:h-20 flex items-center justify-center px-4 max-w-2xl text-center">
          <p className="text-base sm:text-xl font-light text-white leading-relaxed font-sans drop-shadow-[0_2px_16px_rgba(0,0,0,0.7)] min-h-[1.75em]">
            <span>{displayedText}</span>
            <span className="inline-block w-[2px] h-5 sm:h-6 bg-white ml-1.5 animate-pulse align-middle" />
          </p>
        </div>

        {/* Get In Button */}
        <div className="pt-2">
          <Link
            href="/"
            className="group relative inline-flex items-center gap-3 px-8 sm:px-10 py-3.5 sm:py-4 rounded-full text-sm sm:text-base font-medium text-white bg-white/20 hover:bg-white/30 border border-white/50 backdrop-blur-md transition-all duration-300 hover:scale-105 active:scale-95 shadow-[0_8px_32px_rgba(0,0,0,0.35)] hover:shadow-[0_12px_40px_rgba(255,143,177,0.5)]"
          >
            <span className="tracking-wide">Get In</span>
            <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
          </Link>
        </div>
      </div>

      {/* Aesthetic Footer Note */}
      <div className="absolute bottom-6 z-10 text-xs font-mono text-white/50 tracking-wider">
        VERIDION PROTOCOL • SEPOLIA TESTNET
      </div>
    </div>
  );
}
