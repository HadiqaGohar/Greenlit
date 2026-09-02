"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Film, ArrowLeft } from "lucide-react";

interface ShareData {
  script_id: string;
  created_at: string;
  expires_at: string;
  access_count: number;
  report?: {
    risk_assessment?: { overall_risk_score?: number; risk_level?: string };
    risk_score?: number;
    risk_level?: string;
    claims?: Array<{ text: string; verdict: string; confidence: number }>;
    agent_results?: Record<string, { success: boolean; confidence_score: number; processing_time: number }>;
    processing_time?: number;
  };
}

export default function SharePage() {
  const params = useParams();
  const token = params.token as string;
  const [data, setData] = useState<ShareData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchShareData(); }, [token]);

  const fetchShareData = async () => {
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/share/" + token);
      if (!res.ok) { setError(res.status === 404 ? "Link not found" : "Failed to load"); return; }
      setData(await res.json());
    } catch { setError("Server error"); } finally { setLoading(false); }
  };

  const report = data?.report;
  // Handle both nested (risk_assessment.overall_risk_score) and flat (risk_score) formats
  const riskScore = report?.risk_assessment?.overall_risk_score ?? report?.risk_score ?? 0;
  const riskLevel = report?.risk_assessment?.risk_level ?? report?.risk_level ?? "unknown";
  const claims = report?.claims ?? [];
  const agents = report?.agent_results ?? {};
  const verified = claims.filter(c => c.verdict === "verified").length;
  const flagged = claims.filter(c => c.verdict === "flagged").length;

  if (loading) return <div className="min-h-screen flex items-center justify-center" style={{backgroundColor:"var(--bg)"}}><div className="w-16 h-16 rounded-full border-4 border-t-transparent animate-spin" style={{borderColor:"var(--border)",borderTopColor:"transparent"}} /></div>;

  if (error) return <div className="min-h-screen flex items-center justify-center" style={{backgroundColor:"var(--bg)"}}><div className="claim-card rounded-2xl p-8 text-center max-w-md"><AlertTriangle size={32} className="mx-auto mb-4" style={{color:"var(--flagged)"}} /><h1 className="text-2xl font-bold mb-3" style={{color:"var(--text)"}}>Link Unavailable</h1><p className="mb-6" style={{color:"var(--text-muted)"}}>{error}</p><Link href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold" style={{backgroundColor:"var(--accent)",color:"var(--accent-contrast)"}}><ArrowLeft size={16} /> Go to GreenLit AI</Link></div></div>;

  return (
    <div className="min-h-screen" style={{backgroundColor:"var(--bg)"}}>
      <div className="border-b" style={{borderColor:"var(--border)"}}>
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3"><div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{background:"linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)"}}><Film size={20} style={{color:"var(--accent-contrast)"}} /></div><span className="font-display text-xl font-bold" style={{color:"var(--text)"}}>GreenLit AI</span></Link>
          <span className="px-3 py-1 rounded-full text-xs font-medium" style={{backgroundColor:"color-mix(in srgb, var(--accent) 15%, transparent)",color:"var(--accent)"}}>Shared Report</span>
        </div>
      </div>
      <div className="max-w-4xl mx-auto px-6 py-12">
        <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}>
          <div className="claim-card rounded-2xl p-8 mb-6">
            <div className="flex items-start justify-between mb-6"><div><h1 className="font-display text-3xl font-bold mb-2" style={{color:"var(--text)"}}>Script Analysis Report</h1><p className="text-sm" style={{color:"var(--text-muted)"}}>ID: {data?.script_id}</p></div><div className="px-4 py-2 rounded-lg" style={{backgroundColor:"color-mix(in srgb, var(--verified) 15%, transparent)"}}><div className="flex items-center gap-2"><CheckCircle size={16} style={{color:"var(--verified)"}} /><span className="text-sm font-medium" style={{color:"var(--verified)"}}>Verified</span></div></div></div>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-lg" style={{backgroundColor:"var(--bg)"}}><p className="text-xs" style={{color:"var(--text-muted)"}}>Created</p><p className="text-sm font-medium" style={{color:"var(--text)"}}>{data?.created_at ? new Date(data.created_at).toLocaleDateString() : "N/A"}</p></div>
              <div className="p-4 rounded-lg" style={{backgroundColor:"var(--bg)"}}><p className="text-xs" style={{color:"var(--text-muted)"}}>Expires</p><p className="text-sm font-medium" style={{color:"var(--text)"}}>{data?.expires_at ? new Date(data.expires_at).toLocaleDateString() : "Never"}</p></div>
              <div className="p-4 rounded-lg" style={{backgroundColor:"var(--bg)"}}><p className="text-xs" style={{color:"var(--text-muted)"}}>Views</p><p className="text-sm font-medium" style={{color:"var(--text)"}}>{data?.access_count || 0}</p></div>
            </div>
          </div>
          <div className="claim-card rounded-2xl p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4" style={{color:"var(--text)"}}>Risk Assessment</h3>
            <div className="flex items-center gap-6">
              <div className="relative w-24 h-24"><svg className="w-full h-full" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" strokeWidth="8" /><circle cx="50" cy="50" r="40" fill="none" stroke={riskScore<30?"var(--verified)":riskScore<60?"var(--accent)":"var(--flagged)"} strokeWidth="8" strokeDasharray={riskScore*2.51+" 251"} strokeLinecap="round" transform="rotate(-90 50 50)" /></svg><div className="absolute inset-0 flex items-center justify-center"><span className="text-xl font-bold" style={{color:riskScore<30?"var(--verified)":riskScore<60?"var(--accent)":"var(--flagged)"}}>{Math.round(riskScore)}%</span></div></div>
              <div><p className="text-sm" style={{color:"var(--text-muted)"}}>Risk Level</p><p className="text-lg font-semibold capitalize" style={{color:"var(--text)"}}>{riskLevel}</p></div>
            </div>
          </div>
          {claims.length > 0 && <div className="claim-card rounded-2xl p-6 mb-6"><h3 className="text-lg font-semibold mb-4" style={{color:"var(--text)"}}>Claims ({claims.length})</h3><div className="grid grid-cols-3 gap-3 mb-4"><div className="p-3 rounded-lg text-center" style={{backgroundColor:"var(--bg)"}}><p className="text-2xl font-bold" style={{color:"var(--text)"}}>{claims.length}</p><p className="text-xs" style={{color:"var(--text-muted)"}}>Total</p></div><div className="p-3 rounded-lg text-center" style={{backgroundColor:"var(--bg)"}}><p className="text-2xl font-bold" style={{color:"var(--verified)"}}>{verified}</p><p className="text-xs" style={{color:"var(--text-muted)"}}>Verified</p></div><div className="p-3 rounded-lg text-center" style={{backgroundColor:"var(--bg)"}}><p className="text-2xl font-bold" style={{color:"var(--flagged)"}}>{flagged}</p><p className="text-xs" style={{color:"var(--text-muted)"}}>Flagged</p></div></div></div>}
          {Object.keys(agents).length > 0 && <div className="claim-card rounded-2xl p-6 mb-8"><h3 className="text-lg font-semibold mb-4" style={{color:"var(--text)"}}>Agent Performance</h3><div className="grid grid-cols-2 gap-3">{Object.entries(agents).map(([name, a]) => <div key={name} className="p-4 rounded-lg" style={{backgroundColor:"var(--bg)"}}><div className="flex items-center justify-between mb-2"><span className="font-medium capitalize" style={{color:"var(--text)"}}>{name}</span><span className={"px-2 py-0.5 rounded-full text-xs "+(a.success?"bg-green-100 text-green-800":"bg-red-100 text-red-800")}>{a.success?"OK":"Fail"}</span></div><p className="text-xs" style={{color:"var(--text-muted)"}}>Confidence: {(a.confidence_score*100).toFixed(0)}%</p></div>)}</div></div>}
          <div className="text-center"><Link href="/analyze" className="inline-flex items-center gap-2 px-8 py-4 rounded-xl font-semibold transition-all hover:scale-105" style={{background:"linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)",color:"var(--accent-contrast)"}}>Start Free Analysis</Link></div>
        </motion.div>
      </div>
    </div>
  );
}