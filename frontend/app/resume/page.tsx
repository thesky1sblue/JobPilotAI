"use client";
import { useEffect, useState, useRef } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { uploadResume, getProfile, CandidateProfile } from "@/lib/api";
import { Upload, FileText, CheckCircle, User } from "lucide-react";

export default function ResumePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    try { setProfile(await getProfile()); } catch { /* no profile yet */ }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setUploadResult(null);
    try {
      const r = await uploadResume(file);
      setUploadResult(`Resume uploaded successfully (v${r.version})`);
      await load();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Resume Studio" subtitle="Upload, manage and generate tailored resumes" />
      <div className="flex-1 overflow-auto p-6 space-y-6 max-w-3xl">
        {/* Upload section */}
        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
            <Upload size={14} className="text-accent" /> Upload Resume
          </h2>
          <div
            className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-accent/50 transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            <FileText size={32} className="text-text-muted mx-auto mb-3" />
            <p className="text-sm text-text-muted">Click to upload PDF or DOCX</p>
            <p className="text-xs text-text-muted mt-1">Maximum 10MB</p>
            {uploadResult && <p className="text-xs text-success mt-2">{uploadResult}</p>}
            {error && <p className="text-xs text-danger mt-2">{error}</p>}
            {uploading && <p className="text-xs text-accent mt-2">Uploading...</p>}
          </div>
          <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleUpload} />
        </div>

        {/* Profile */}
        {profile && (
          <div className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-xs font-semibold text-text uppercase tracking-wider mb-4 flex items-center gap-2">
              <User size={14} className="text-accent" /> Candidate Profile
            </h2>
            <div className="grid grid-cols-2 gap-3 text-xs mb-4">
              <div><span className="text-text-muted">Name: </span><span className="text-text">{profile.full_name}</span></div>
              <div><span className="text-text-muted">Email: </span><span className="text-text">{profile.email}</span></div>
              <div><span className="text-text-muted">Location: </span><span className="text-text">{profile.location || "—"}</span></div>
              <div><span className="text-text-muted">Experience: </span><span className="text-text">{profile.experience_years}y</span></div>
            </div>
            
            {profile.facts && profile.facts.length > 0 && (
              <div>
                <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Extracted Facts ({profile.facts.length})</h3>
                <div className="space-y-1">
                  {profile.facts.map(f => (
                    <div key={f.id} className="flex items-center gap-2 text-xs">
                      {f.verified && <CheckCircle size={10} className="text-success" />}
                      <span className="text-text-muted capitalize">{f.type}:</span>
                      <span className="text-text font-mono">{JSON.stringify(f.data).slice(0, 60)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!profile && (
          <div className="text-center p-8 text-text-muted text-xs">
            Upload your resume to create your candidate profile.
          </div>
        )}
      </div>
    </div>
  );
}