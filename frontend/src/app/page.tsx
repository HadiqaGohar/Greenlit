"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative px-6 py-24 text-center">
        <div className="mx-auto max-w-4xl">
          <h1 className="font-display text-6xl font-bold tracking-tight mb-6" 
              style={{ color: 'var(--text)' }}>
            <span className="marquee-text">GreenLit AI</span>
          </h1>
          <p className="text-xl mb-8 max-w-2xl mx-auto" 
             style={{ color: 'var(--text-muted)' }}>
            AI-powered fact-checking for film and TV scripts. Extract claims, 
            verify facts, and get production notes with live research sources.
          </p>
          <Link 
            href="/analyze"
            className="cta-button inline-flex items-center px-8 py-4 rounded-lg text-lg font-semibold transition-all hover:transform hover:scale-105"
            style={{
              backgroundColor: 'var(--accent)',
              color: 'var(--accent-contrast)'
            }}
          >
            Start Analysis
          </Link>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-display text-4xl font-bold text-center mb-16" 
              style={{ color: 'var(--text)' }}>
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="claim-card rounded-lg p-8 text-center">
              <div className="countdown-number text-4xl mb-4" 
                   style={{ color: 'var(--accent)' }}>
                1
              </div>
              <h3 className="font-display text-xl font-semibold mb-3" 
                  style={{ color: 'var(--text)' }}>
                Paste Your Script
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Upload scenes, dialogue, or full scripts. Our AI extracts factual 
                claims automatically.
              </p>
            </div>
            
            <div className="claim-card rounded-lg p-8 text-center">
              <div className="countdown-number text-4xl mb-4" 
                   style={{ color: 'var(--accent)' }}>
                2
              </div>
              <h3 className="font-display text-xl font-semibold mb-3" 
                  style={{ color: 'var(--text)' }}>
                Live Fact-Checking
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Claims are researched in real-time using multiple sources 
                for accuracy verification.
              </p>
            </div>
            
            <div className="claim-card rounded-lg p-8 text-center">
              <div className="countdown-number text-4xl mb-4" 
                   style={{ color: 'var(--accent)' }}>
                3
              </div>
              <h3 className="font-display text-xl font-semibold mb-3" 
                  style={{ color: 'var(--text)' }}>
                Production Notes
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Get detailed reports with confidence scores, sources, 
                and suggested fixes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="px-6 py-16 text-center">
        <div className="mx-auto max-w-2xl">
          <h2 className="font-display text-3xl font-bold mb-6" 
              style={{ color: 'var(--text)' }}>
            Ready to Green Light Your Script?
          </h2>
          <p className="text-lg mb-8" 
             style={{ color: 'var(--text-muted)' }}>
            Join filmmakers using AI to catch errors before they become costly mistakes.
          </p>
          <Link 
            href="/analyze"
            className="cta-button inline-flex items-center px-8 py-4 rounded-lg text-lg font-semibold transition-all hover:transform hover:scale-105"
            style={{
              backgroundColor: 'var(--accent)',
              color: 'var(--accent-contrast)'
            }}
          >
            Analyze Your First Script
          </Link>
        </div>
      </section>
    </div>
  );
}
