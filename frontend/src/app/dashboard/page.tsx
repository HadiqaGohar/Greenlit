"use client";

import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useEffect, useState } from 'react';

interface Report {
  id: string;
  title: string;
  date: string;
  claimCount: number;
  flaggedCount: number;
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

  useEffect(() => {
    // In a real app, this would fetch from Firebase/Firestore
    // For now, using mock data
    const mockReports: Report[] = [];
    setReports(mockReports);
    
    setStats({
      totalScripts: mockReports.length,
      totalClaims: mockReports.reduce((sum, report) => sum + report.claimCount, 0),
      verifiedClaims: 0,
      flaggedClaims: mockReports.reduce((sum, report) => sum + report.flaggedCount, 0)
    });
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-10">
        <h1 className="font-display text-4xl font-bold mb-2" 
            style={{ color: 'var(--text)' }}>
          Welcome back, {user?.displayName || user?.email?.split('@')[0]}
        </h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Your script analysis dashboard
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <div className="claim-card rounded-lg p-6">
          <div className="text-2xl font-bold mb-1" 
               style={{ color: 'var(--accent)' }}>
            {stats.totalScripts}
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Scripts Analyzed
          </div>
        </div>

        <div className="claim-card rounded-lg p-6">
          <div className="text-2xl font-bold mb-1" 
               style={{ color: 'var(--text)' }}>
            {stats.totalClaims}
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Total Claims
          </div>
        </div>

        <div className="claim-card rounded-lg p-6">
          <div className="text-2xl font-bold mb-1" 
               style={{ color: 'var(--verified)' }}>
            {stats.verifiedClaims}
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Verified Claims
          </div>
        </div>

        <div className="claim-card rounded-lg p-6">
          <div className="text-2xl font-bold mb-1" 
               style={{ color: 'var(--flagged)' }}>
            {stats.flaggedClaims}
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Flagged Claims
          </div>
        </div>
      </div>

      {/* Recent Reports */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-display text-2xl font-bold" 
              style={{ color: 'var(--text)' }}>
            Recent Reports
          </h2>
          <Link 
            href="/analyze"
            className="px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
            style={{
              backgroundColor: 'var(--accent)',
              color: 'var(--accent-contrast)'
            }}
          >
            Analyze New Script
          </Link>
        </div>

        {reports.length === 0 ? (
          <div className="claim-card rounded-lg p-12 text-center">
            <div className="text-4xl mb-4">🎬</div>
            <h3 className="font-display text-xl font-semibold mb-2" 
                style={{ color: 'var(--text)' }}>
              No scripts analyzed yet
            </h3>
            <p className="mb-6" style={{ color: 'var(--text-muted)' }}>
              Get started by analyzing your first script to see detailed fact-checking reports.
            </p>
            <Link 
              href="/analyze"
              className="inline-flex items-center px-6 py-3 rounded-lg text-sm font-semibold transition-colors"
              style={{
                backgroundColor: 'var(--accent)',
                color: 'var(--accent-contrast)'
              }}
            >
              Analyze Your First Script
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div key={report.id} 
                   className="claim-card rounded-lg p-6 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold mb-1" 
                      style={{ color: 'var(--text)' }}>
                    {report.title}
                  </h3>
                  <p className="text-sm mb-2" 
                     style={{ color: 'var(--text-muted)' }}>
                    {formatDate(report.date)}
                  </p>
                  <div className="flex gap-4 text-sm">
                    <span style={{ color: 'var(--text-muted)' }}>
                      {report.claimCount} claims
                    </span>
                    {report.flaggedCount > 0 && (
                      <span style={{ color: 'var(--flagged)' }}>
                        {report.flaggedCount} flagged
                      </span>
                    )}
                  </div>
                </div>
                <Link 
                  href={`/report/${report.id}`}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors border"
                  style={{
                    border: '1px solid var(--border)',
                    color: 'var(--text)'
                  }}
                >
                  View Report
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
