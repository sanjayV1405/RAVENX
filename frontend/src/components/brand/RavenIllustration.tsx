"use client";

import React from "react";

export function RavenIllustration({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 520 340"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        {/* Shadow and glow filters */}
        <filter id="ravenGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#DC2626" floodOpacity="0.3" />
        </filter>
        <linearGradient id="featherRed1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#EF4444" />
          <stop offset="50%" stopColor="#DC2626" />
          <stop offset="100%" stopColor="#991B1B" />
        </linearGradient>
        <linearGradient id="featherRed2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F87171" />
          <stop offset="70%" stopColor="#DC2626" />
          <stop offset="100%" stopColor="#7F1D1D" />
        </linearGradient>
        <linearGradient id="charcoalFacet1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#282E3E" />
          <stop offset="100%" stopColor="#12151D" />
        </linearGradient>
        <linearGradient id="charcoalFacet2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1E2330" />
          <stop offset="100%" stopColor="#0B0D12" />
        </linearGradient>
        <linearGradient id="charcoalFacet3" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#373F54" />
          <stop offset="100%" stopColor="#181D28" />
        </linearGradient>
        <linearGradient id="eyeRuby" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF6B6B" />
          <stop offset="50%" stopColor="#DC2626" />
          <stop offset="100%" stopColor="#991B1B" />
        </linearGradient>
      </defs>

      {/* Atmospheric Crimson Energy Streaks / Wing Shards radiating backwards */}
      <g filter="url(#ravenGlow)" opacity="0.95">
        {/* Radiating wing crystals */}
        <polygon points="260,110 370,55 330,120" fill="url(#featherRed1)" />
        <polygon points="310,95 440,40 370,115" fill="url(#featherRed2)" />
        <polygon points="340,115 480,75 390,140" fill="url(#featherRed1)" />
        <polygon points="370,135 510,130 405,175" fill="url(#featherRed2)" />
        <polygon points="360,165 490,210 375,205" fill="url(#featherRed1)" />
        <polygon points="320,190 440,270 335,225" fill="url(#featherRed2)" />
      </g>

      {/* Lower Secondary Crimson Glow Shards */}
      <polygon points="250,220 310,290 280,230" fill="url(#featherRed1)" opacity="0.8" />
      <polygon points="200,240 250,320 230,245" fill="url(#featherRed2)" opacity="0.75" />

      {/* Low-Poly Faceted 3D Raven Head & Body */}
      {/* Crown / Top of head */}
      <polygon points="175,60 235,95 205,120 145,85" fill="url(#charcoalFacet3)" />
      <polygon points="235,95 285,110 245,145 205,120" fill="url(#charcoalFacet1)" />
      <polygon points="285,110 335,130 275,170 245,145" fill="url(#charcoalFacet2)" />

      {/* Upper Beak (Sharp, Aggressive, Pointed Left) */}
      <polygon points="20,145 105,115 155,140" fill="url(#charcoalFacet1)" />
      <polygon points="20,145 155,140 140,165" fill="url(#charcoalFacet2)" />

      {/* Forehead / Brow */}
      <polygon points="105,115 175,60 145,85 155,140" fill="url(#charcoalFacet3)" />
      <polygon points="145,85 205,120 170,150 155,140" fill="url(#charcoalFacet2)" />

      {/* Eye Socket & Ruby Eye */}
      <polygon points="155,140 170,150 162,142" fill="#0C0E14" />
      {/* Ruby Eye Polygon */}
      <polygon points="142,130 158,124 154,136 138,135" fill="url(#eyeRuby)" filter="url(#ravenGlow)" />
      <polygon points="146,131 150,129 148,133" fill="#FFFFFF" opacity="0.9" />

      {/* Cheek & Jaw */}
      <polygon points="20,145 140,165 110,190" fill="#080A0E" />
      <polygon points="140,165 180,185 145,210 110,190" fill="url(#charcoalFacet1)" />
      <polygon points="170,150 220,165 180,185 140,165" fill="url(#charcoalFacet3)" />

      {/* Mid Neck & Body Facets */}
      <polygon points="205,120 245,145 230,190 170,150" fill="url(#charcoalFacet1)" />
      <polygon points="245,145 275,170 240,215 230,190" fill="#0F1218" />
      <polygon points="220,165 255,200 215,225 180,185" fill="url(#charcoalFacet2)" />

      {/* Crimson Crest Accent Feathers on Head */}
      <polygon points="205,120 245,145 260,110 235,95" fill="url(#featherRed1)" />
      <polygon points="245,145 275,170 300,135 285,110" fill="url(#featherRed2)" />

      {/* Lower Neck / Breast Facets */}
      <polygon points="180,185 215,225 185,260 145,210" fill="url(#charcoalFacet3)" />
      <polygon points="215,225 255,200 240,270 185,260" fill="url(#charcoalFacet1)" />
      <polygon points="255,200 275,170 285,235 240,270" fill="#0A0C10" />

      {/* Throat Crimson Feather Highlights */}
      <polygon points="240,215 285,235 260,265" fill="url(#featherRed1)" />
      <polygon points="240,270 285,285 255,305 215,285" fill="url(#featherRed2)" />
      <polygon points="185,260 215,285 175,315 150,270" fill="url(#charcoalFacet2)" />

      {/* Subtle Specular Highlights */}
      <line x1="20" y1="145" x2="105" y2="115" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
      <line x1="105" y1="115" x2="175" y2="60" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
      <line x1="175" y1="60" x2="235" y2="95" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
    </svg>
  );
}

export default RavenIllustration;

