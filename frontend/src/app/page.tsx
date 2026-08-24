"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import {
  Film,
  Search,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  Users,
  Zap,
  Shield,
  ArrowRight,
  Play,
  Star,
} from "lucide-react";
import { SampleScriptLibrary } from "@/components/SampleScriptLibrary";

function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      opacity: number;
    }> = [];

    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 2 + 1,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }

    function animate() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(59, 130, 246, ${p.opacity})`;
        ctx.fill();
      });

      // Draw connections
      particles.forEach((p1, i) => {
        particles.slice(i + 1).forEach((p2) => {
          const dist = Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - dist / 150)})`;
            ctx.stroke();
          }
        });
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ opacity: 0.6 }}
    />
  );
}

function FloatingCard({
  icon: Icon,
  title,
  value,
  color,
  delay,
}: {
  icon: any;
  title: string;
  value: string;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
      className="claim-card rounded-xl p-6 backdrop-blur-sm"
      style={{
        border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 5%, var(--bg)) 0%, var(--bg) 100%)`,
      }}
    >
      <div className="flex items-center gap-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)` }}
        >
          <Icon size={24} style={{ color }} />
        </div>
        <div>
          <p className="text-2xl font-bold" style={{ color: "var(--text)" }}>
            {value}
          </p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {title}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
  color,
  index,
}: {
  icon: any;
  title: string;
  description: string;
  color: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      whileHover={{ y: -5, scale: 1.02 }}
      className="claim-card rounded-xl p-6 cursor-pointer group"
    >
      <div
        className="w-14 h-14 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
        style={{ backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)` }}
      >
        <Icon size={28} style={{ color }} />
      </div>
      <h3
        className="font-display text-xl font-semibold mb-2"
        style={{ color: "var(--text)" }}
      >
        {title}
      </h3>
      <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
        {description}
      </p>
    </motion.div>
  );
}

function StepCard({
  number,
  title,
  description,
  index,
}: {
  number: string;
  title: string;
  description: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -30 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.2 }}
      className="relative"
    >
      <div className="flex items-start gap-6">
        <div className="flex-shrink-0">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold"
            style={{
              background: "linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, #8b5cf6) 100%)",
              color: "var(--accent-contrast)",
            }}
          >
            {number}
          </div>
        </div>
        <div className="flex-1 pt-2">
          <h3
            className="font-display text-xl font-semibold mb-2"
            style={{ color: "var(--text)" }}
          >
            {title}
          </h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
            {description}
          </p>
        </div>
      </div>
      {index < 2 && (
        <div
          className="absolute left-8 top-20 w-0.5 h-16"
          style={{ backgroundColor: "var(--border)" }}
        />
      )}
    </motion.div>
  );
}

export default function HomePage() {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);

  const [currentTestimonial, setCurrentTestimonial] = useState(0);

  const testimonials = [
    {
      quote: "GreenLit AI caught a historical error that would have cost us $50K in reshoots.",
      author: "Sarah Chen",
      role: "Producer, Sunset Pictures",
    },
    {
      quote: "The multi-agent system is incredible. It's like having a team of researchers working 24/7.",
      author: "Marcus Rodriguez",
      role: "Director, Indie Films Co",
    },
    {
      quote: "We reduced our pre-production research time by 60% using GreenLit AI.",
      author: "Emily Thompson",
      role: "Head of Development, Nova Studios",
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen overflow-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center">
        <ParticleBackground />

        {/* Gradient overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, transparent 0%, var(--bg) 70%)",
          }}
        />

        <motion.div
          style={{ y, opacity }}
          className="relative z-10 text-center px-6 max-w-5xl mx-auto"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="mb-6"
          >
            <span
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
              style={{
                backgroundColor: "color-mix(in srgb, var(--accent) 10%, transparent)",
                color: "var(--accent)",
                border: "1px solid color-mix(in srgb, var(--accent) 30%, transparent)",
              }}
            >
              <Zap size={14} />
              AI-Powered Script Analysis
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="font-display text-6xl md:text-8xl font-bold tracking-tight mb-6"
            style={{ color: "var(--text)" }}
          >
            <span className="block">GreenLit</span>
            <span
              className="block"
              style={{
                background: "linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              AI
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl md:text-2xl mb-10 max-w-3xl mx-auto leading-relaxed"
            style={{ color: "var(--text-muted)" }}
          >
            Upload your screenplay → 4 AI agents analyze it in parallel → Get a
            production-ready report with legal risks, fact-checking, and
            continuity issues.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link
              href="/analyze"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105"
              style={{
                background: "linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, #8b5cf6) 100%)",
                color: "var(--accent-contrast)",
                boxShadow: "0 10px 40px color-mix(in srgb, var(--accent) 30%, transparent)",
              }}
            >
              <Play size={20} />
              Start Analyzing
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105"
              style={{
                backgroundColor: "var(--bg)",
                color: "var(--text)",
                border: "1px solid var(--border)",
              }}
            >
              View Dashboard
              <ArrowRight size={20} />
            </Link>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto"
          >
            {[
              { value: "10K+", label: "Scripts Analyzed" },
              { value: "99.2%", label: "Accuracy Rate" },
              { value: "50+", label: "Production Studios" },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <p
                  className="text-3xl font-bold"
                  style={{ color: "var(--accent)" }}
                >
                  {stat.value}
                </p>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  {stat.label}
                </p>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-6 h-10 rounded-full border-2 flex items-start justify-center p-1"
            style={{ borderColor: "var(--border)" }}
          >
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-1.5 h-3 rounded-full"
              style={{ backgroundColor: "var(--accent)" }}
            />
          </motion.div>
        </motion.div>
      </section>

      {/* Floating Stats */}
      <section className="relative py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <FloatingCard
              icon={CheckCircle}
              title="Claims Verified"
              value="45,892"
              color="#10b981"
              delay={0}
            />
            <FloatingCard
              icon={AlertTriangle}
              title="Errors Caught"
              value="2,341"
              color="#f59e0b"
              delay={0.1}
            />
            <FloatingCard
              icon={BarChart3}
              title="Reports Generated"
              value="8,567"
              color="#3b82f6"
              delay={0.2}
            />
            <FloatingCard
              icon={Users}
              title="Active Teams"
              value="312"
              color="#8b5cf6"
              delay={0.3}
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2
              className="font-display text-4xl md:text-5xl font-bold mb-4"
              style={{ color: "var(--text)" }}
            >
              Powerful Features
            </h2>
            <p
              className="text-lg max-w-2xl mx-auto"
              style={{ color: "var(--text-muted)" }}
            >
              Everything you need to ensure your script is production-ready
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={Search}
              title="Multi-Agent Analysis"
              description="Four specialized AI agents work in parallel to analyze different aspects of your script."
              color="#3b82f6"
              index={0}
            />
            <FeatureCard
              icon={Shield}
              title="Legal Compliance"
              description="Automatically detect potential legal issues, copyright concerns, and liability risks."
              color="#ef4444"
              index={1}
            />
            <FeatureCard
              icon={Film}
              title="Continuity Checking"
              description="Ensure scene consistency, character arcs, and timeline accuracy throughout your script."
              color="#10b981"
              index={2}
            />
            <FeatureCard
              icon={BarChart3}
              title="Risk Assessment"
              description="Visual risk gauges and detailed reports help you prioritize issues before production."
              color="#f59e0b"
              index={3}
            />
            <FeatureCard
              icon={Users}
              title="Team Collaboration"
              description="Real-time collaboration with your team through comments, annotations, and shared notes."
              color="#8b5cf6"
              index={4}
            />
            <FeatureCard
              icon={Zap}
              title="Instant Results"
              description="Get comprehensive analysis in seconds, not days. Accelerate your pre-production workflow."
              color="#06b6d4"
              index={5}
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6" style={{ backgroundColor: "var(--bg-secondary, var(--bg))" }}>
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2
              className="font-display text-4xl md:text-5xl font-bold mb-4"
              style={{ color: "var(--text)" }}
            >
              How It Works
            </h2>
            <p
              className="text-lg max-w-2xl mx-auto"
              style={{ color: "var(--text-muted)" }}
            >
              Three simple steps to production-ready scripts
            </p>
          </motion.div>

          <div className="space-y-12">
            <StepCard
              number="1"
              title="Upload Your Script"
              description="Drag and drop your script or paste it directly. We support .txt, .pdf, .fdx, and .fountain formats."
              index={0}
            />
            <StepCard
              number="2"
              title="AI Analysis in Progress"
              description="Our multi-agent system analyzes claims, checks legal issues, verifies continuity, and assesses risks in parallel."
              index={1}
            />
            <StepCard
              number="3"
              title="Review & Export"
              description="Get a comprehensive report with confidence scores, sources, and suggested fixes. Export as PDF, JSON, or share with your team."
              index={2}
            />
          </div>
        </div>
      </section>

      {/* Sample Scripts - Try It Now */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <SampleScriptLibrary />
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2
              className="font-display text-4xl md:text-5xl font-bold mb-4"
              style={{ color: "var(--text)" }}
            >
              Trusted by Filmmakers
            </h2>
          </motion.div>

          <div className="relative">
            <motion.div
              key={currentTestimonial}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              className="claim-card rounded-2xl p-8 md:p-12 text-center"
            >
              <div className="flex justify-center mb-6">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star
                    key={i}
                    size={24}
                    fill="var(--accent)"
                    style={{ color: "var(--accent)" }}
                  />
                ))}
              </div>
              <p
                className="text-xl md:text-2xl font-medium mb-8 italic"
                style={{ color: "var(--text)" }}
              >
                &ldquo;{testimonials[currentTestimonial].quote}&rdquo;
              </p>
              <div>
                <p
                  className="font-semibold"
                  style={{ color: "var(--text)" }}
                >
                  {testimonials[currentTestimonial].author}
                </p>
                <p
                  className="text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  {testimonials[currentTestimonial].role}
                </p>
              </div>
            </motion.div>

            {/* Dots */}
            <div className="flex justify-center gap-2 mt-6">
              {testimonials.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentTestimonial(i)}
                  className="w-2 h-2 rounded-full transition-all"
                  style={{
                    backgroundColor:
                      i === currentTestimonial ? "var(--accent)" : "var(--border)",
                    width: i === currentTestimonial ? "24px" : "8px",
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="rounded-3xl p-12 md:p-16"
            style={{
              background:
                "linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, #8b5cf6) 100%)",
            }}
          >
            <h2
              className="font-display text-4xl md:text-5xl font-bold mb-6"
              style={{ color: "var(--accent-contrast)" }}
            >
              Ready to Green Light Your Script?
            </h2>
            <p
              className="text-lg mb-10 max-w-2xl mx-auto"
              style={{ color: "color-mix(in srgb, var(--accent-contrast) 80%, transparent)" }}
            >
              Join thousands of filmmakers using AI to catch errors before they
              become costly mistakes.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/analyze"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105"
                style={{
                  backgroundColor: "var(--accent-contrast)",
                  color: "var(--accent)",
                }}
              >
                <Play size={20} />
                Start Free Analysis
              </Link>
              <Link
                href="/analytics"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105"
                style={{
                  backgroundColor: "transparent",
                  color: "var(--accent-contrast)",
                  border: "2px solid var(--accent-contrast)",
                }}
              >
                View Analytics
                <ArrowRight size={20} />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6" style={{ borderTop: "1px solid var(--border)" }}>
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{
                  background: "linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)",
                }}
              >
                <Film size={20} style={{ color: "var(--accent-contrast)" }} />
              </div>
              <span
                className="font-display text-xl font-bold"
                style={{ color: "var(--text)" }}
              >
                GreenLit AI
              </span>
            </div>
            <div className="flex gap-6">
              <Link
                href="/analyze"
                className="text-sm hover:opacity-80 transition-opacity"
                style={{ color: "var(--text-muted)" }}
              >
                Analyze
              </Link>
              <Link
                href="/dashboard"
                className="text-sm hover:opacity-80 transition-opacity"
                style={{ color: "var(--text-muted)" }}
              >
                Dashboard
              </Link>
              <Link
                href="/analytics"
                className="text-sm hover:opacity-80 transition-opacity"
                style={{ color: "var(--text-muted)" }}
              >
                Analytics
              </Link>
            </div>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              &copy; 2026 GreenLit AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
