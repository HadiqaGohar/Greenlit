"use client";

import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useOnboardingProgress, useLoadedSamples } from '@/hooks/useSampleLoader';
import { TUTORIAL_STEPS, SAMPLE_SCRIPTS } from '@/lib/sampleData';
import GuidedTour from '@/components/GuidedTour';
import OnboardingBanner from '@/components/dashboard/OnboardingBanner';
import SampleScriptsPanel from '@/components/dashboard/SampleScriptsPanel';
import { listReports } from '@/lib/api';
import { motion } from 'framer-motion';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Clock,
  Zap,
  Plus,
  ArrowRight,
  Film,
} from 'lucide-react';

interface Report {
  id: string;
  title: string;
  date: string;
  claimCount: number;
  flaggedCount: number;
  riskScore?: number;
  status?: string;
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  change,
  index,
}: {
  icon: React.ComponentType<{ size?: string | number; style?: React.CSSProperties }>;
  label: string;
  value: string | number;
  color: string;
  change?: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="claim-card rounded-xl p-5 group hover:scale-[1.02] transition-transform"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: 'var(--text-muted)' }}>
            {label}
          </p>
          <p className="text-3xl font-bold" style={{ color: 'var(--text)' }}>
            {value}
          </p>
          {change && (
            <p className="text-xs mt-2 flex items-center gap-1" style={{ color: 'var(--verified)' }}>
              <TrendingUp size={12} />
              {change}
            </p>
          )}
        </div>
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110"
          style={{ backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)` }}
        >
          <Icon size={24} style={{ color }} />
        </div>
      </div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState({
    totalScripts: 0,
    totalClaims: 0,
    verifiedClaims: 0,
    flaggedClaims: 0
  });

  const { hasCompletedOnboarding } = useOnboardingProgress();
  const { hasSamplesLoaded, loadedSamples } = useLoadedSamples();
  const [showTour, setShowTour] = useState(false);

  useEffect(() => {
    async function fetchReports() {
      try {
        // Fetch real reports from backend, filtered by current user
        const { reports: backendReports } = await listReports(user?.uid);
        
        // Convert backend reports to our format
        const realReports: Report[] = backendReports.map(r => ({
          id: r.id,
          title: r.title,
          date: r.date,
          claimCount: r.claimCount,
          flaggedCount: r.flaggedCount,
          riskScore: r.riskScore,
          status: r.status
        }));
        
        // Also add sample reports that were loaded
        const sampleReports = SAMPLE_SCRIPTS
          .filter(sample => loadedSamples.includes(sample.id))
          .map(sample => ({
            id: sample.id,
            title: sample.title,
            date: new Date().toISOString(),
            claimCount: sample.analysisResults.overview.totalClaims,
            flaggedCount: sample.analysisResults.overview.flaggedClaims,
            status: 'completed'
          }));

        // Combine: real reports first, then samples (avoid duplicates)
        const sampleIds = new Set(sampleReports.map(s => s.id));
        const uniqueRealReports = realReports.filter(r => !sampleIds.has(r.id));
        const allReports = [...uniqueRealReports, ...sampleReports];
        
        setReports(allReports);
        
        setStats({
          totalScripts: allReports.length,
          totalClaims: allReports.reduce((sum, report) => sum + report.claimCount, 0),
          verifiedClaims: sampleReports.reduce((sum, report) => {
            const sample = SAMPLE_SCRIPTS.find(s => s.id === report.id);
            return sum + (sample?.analysisResults.overview.verifiedClaims || 0);
          }, 0),
          flaggedClaims: allReports.reduce((sum, report) => sum + report.flaggedCount, 0)
        });
      } catch (err) {
        console.error('Failed to fetch reports from backend:', err);
        // Fallback to sample reports only
        const sampleReports = SAMPLE_SCRIPTS
          .filter(sample => loadedSamples.includes(sample.id))
          .map(sample => ({
            id: sample.id,
            title: sample.title,
            date: new Date().toISOString(),
            claimCount: sample.analysisResults.overview.totalClaims,
            flaggedCount: sample.analysisResults.overview.flaggedClaims,
            status: 'completed'
          }));
        setReports(sampleReports);
      }
    }
    
    fetchReports();
  }, [loadedSamples, user?.uid]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleStartTour = () => setShowTour(true);
  const handleTourComplete = () => setShowTour(false);
  const handleTourClose = () => setShowTour(false);

  const isNewUser = !hasCompletedOnboarding && !hasSamplesLoaded;

  return (
    <div className="min-h-screen">
      {/* Hero Header */}
      <div className="relative overflow-hidden" style={{ backgroundColor: 'var(--surface)' }}>
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: 'radial-gradient(ellipse at top right, color-mix(in srgb, var(--accent) 20%, transparent), transparent 60%)',
          }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6"
          >
            <div>
              <h1 className="font-display text-4xl font-bold mb-2" style={{ color: 'var(--text)' }}>
                Welcome back,{' '}
                <span className="gradient-text">
                  {user?.displayName || user?.email?.split('@')[0]}
                </span>
              </h1>
              <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
                Your script analysis dashboard
              </p>
            </div>
            <Link
              href="/analyze"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, #8b5cf6) 100%)',
                color: 'var(--accent-contrast)',
                boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 30%, transparent)',
              }}
            >
              <Plus size={20} />
              Analyze New Script
            </Link>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Onboarding Banner */}
        <OnboardingBanner onStartTour={handleStartTour} />

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={FileText}
            label="Total Scripts"
            value={stats.totalScripts}
            color="#3b82f6"
            change="+2 this week"
            index={0}
          />
          <StatCard
            icon={CheckCircle}
            label="Claims Verified"
            value={stats.verifiedClaims}
            color="#10b981"
            change="+12 this week"
            index={1}
          />
          <StatCard
            icon={AlertTriangle}
            label="Flagged Claims"
            value={stats.flaggedClaims}
            color="#ef4444"
            change="-3 vs last week"
            index={2}
          />
          <StatCard
            icon={Zap}
            label="Risk Score"
            value={`${stats.totalClaims > 0 ? Math.round((stats.flaggedClaims / stats.totalClaims) * 100) : 0}%`}
            color="#f59e0b"
            index={3}
          />
        </div>

        {/* Sample Scripts Panel for New Users */}
        {(isNewUser || reports.length === 0) && (
          <div className="mb-8">
            <SampleScriptsPanel />
          </div>
        )}

        {/* Recent Reports */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Recent Reports
            </h2>
            {reports.length > 0 && (
              <Link
                href="/analytics"
                className="text-sm font-medium flex items-center gap-1 hover:opacity-80 transition-opacity"
                style={{ color: 'var(--accent)' }}
              >
                View All
                <ArrowRight size={14} />
              </Link>
            )}
          </div>

          {reports.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="claim-card rounded-2xl p-12 text-center"
            >
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center" style={{ backgroundColor: 'color-mix(in srgb, var(--accent) 10%, transparent)' }}>
                <Film size={40} style={{ color: 'var(--accent)' }} />
              </div>
              <h3 className="font-display text-2xl font-semibold mb-3" style={{ color: 'var(--text)' }}>
                No scripts analyzed yet
              </h3>
              <p className="mb-8 max-w-md mx-auto" style={{ color: 'var(--text-muted)' }}>
                Get started by analyzing your first script or trying our sample scripts to see how GreenLit AI works.
              </p>
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Link
                  href="/analyze"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:scale-105"
                  style={{
                    background: 'linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, #8b5cf6) 100%)',
                    color: 'var(--accent-contrast)',
                  }}
                >
                  <FileText size={20} />
                  Analyze Your Script
                </Link>
                <button
                  onClick={handleStartTour}
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:scale-105"
                  style={{
                    backgroundColor: 'var(--bg)',
                    color: 'var(--text)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <Zap size={20} />
                  Take Tour
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-3">
              {reports.map((report, i) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="claim-card rounded-xl p-5 group hover:scale-[1.01] transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center"
                        style={{
                          backgroundColor: report.flaggedCount > 0
                            ? 'color-mix(in srgb, var(--flagged) 10%, transparent)'
                            : 'color-mix(in srgb, var(--verified) 10%, transparent)',
                        }}
                      >
                        {report.flaggedCount > 0 ? (
                          <AlertTriangle size={20} style={{ color: 'var(--flagged)' }} />
                        ) : (
                          <CheckCircle size={20} style={{ color: 'var(--verified)' }} />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                          {report.title}
                        </h3>
                        <div className="flex items-center gap-3 mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {formatDate(report.date)}
                          </span>
                          <span>{report.claimCount} claims</span>
                          {report.flaggedCount > 0 && (
                            <span style={{ color: 'var(--flagged)' }}>
                              {report.flaggedCount} flagged
                            </span>
                          )}
                          {report.riskScore !== undefined && report.riskScore > 0 && (
                            <span style={{ color: report.riskScore > 70 ? 'var(--flagged)' : 'var(--verified)' }}>
                              Risk: {Math.round(report.riskScore)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Link
                      href={`/report/${report.id}`}
                      className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
                      style={{
                        backgroundColor: 'var(--bg)',
                        color: 'var(--text)',
                        border: '1px solid var(--border)',
                      }}
                    >
                      View Report
                    </Link>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Help Section */}
        {!isNewUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="claim-card rounded-2xl p-8 text-center"
          >
            <h3 className="font-display text-xl font-semibold mb-2" style={{ color: 'var(--text)' }}>
              Need help getting started?
            </h3>
            <p className="mb-6" style={{ color: 'var(--text-muted)' }}>
              Take a quick tour to learn about all the features GreenLit AI offers.
            </p>
            <button
              onClick={handleStartTour}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all hover:scale-105"
              style={{
                backgroundColor: 'var(--bg)',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
            >
              <Zap size={16} />
              Restart Tutorial
            </button>
          </motion.div>
        )}
      </div>

      {/* Guided Tour */}
      <GuidedTour
        steps={TUTORIAL_STEPS}
        isOpen={showTour}
        onClose={handleTourClose}
        onComplete={handleTourComplete}
      />
    </div>
  );
}
