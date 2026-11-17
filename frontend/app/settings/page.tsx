"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getPreferences, updatePreferences, Preferences } from "@/lib/api";
import { Save } from "lucide-react";

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getPreferences().then(setPrefs).catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!prefs) return;
    setSaving(true);
    try {
      await updatePreferences(prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  if (!prefs) return (
    <div className="flex flex-col h-full">
      <TopBar title="Settings" />
      <div className="p-12 text-center text-text-muted text-xs">Loading...</div>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Settings" subtitle="Configure JobPilot AI preferences" />
      <div className="flex-1 overflow-auto p-6 space-y-6 max-w-2xl">
        
        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider">Job Preferences</h2>
          
          <div>
            <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Experience Level</label>
            <select className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent"
              value={prefs.experience_level}
              onChange={e => setPrefs({ ...prefs, experience_level: e.target.value })}>
              <option value="fresher">Fresher / 0–1 year</option>
              <option value="junior">Junior / 1–3 years</option>
              <option value="mid">Mid-level / 3–5 years</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Target Roles (one per line)</label>
            <textarea
              className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent font-mono"
              rows={6}
              value={prefs.target_roles.join("\n")}
              onChange={e => setPrefs({ ...prefs, target_roles: e.target.value.split("\n").filter(Boolean) })}
            />
          </div>

          <div>
            <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Preferred Locations (one per line)</label>
            <textarea
              className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent font-mono"
              rows={5}
              value={prefs.preferred_locations.join("\n")}
              onChange={e => setPrefs({ ...prefs, preferred_locations: e.target.value.split("\n").filter(Boolean) })}
            />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider">Discovery Schedule</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Morning (IST)</label>
              <input type="time" className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent"
                value={prefs.discovery_morning}
                onChange={e => setPrefs({ ...prefs, discovery_morning: e.target.value })} />
            </div>
            <div>
              <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Evening (IST)</label>
              <input type="time" className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent"
                value={prefs.discovery_evening}
                onChange={e => setPrefs({ ...prefs, discovery_evening: e.target.value })} />
            </div>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider">LLM Configuration</h2>
          <div>
            <label className="text-[11px] text-text-muted uppercase tracking-wider block mb-1">Provider</label>
            <select className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent"
              value={prefs.llm_provider}
              onChange={e => setPrefs({ ...prefs, llm_provider: e.target.value })}>
              <option value="gemini">Google Gemini</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>
          <p className="text-[11px] text-text-muted">API keys are configured via environment variables (GEMINI_API_KEY / ANTHROPIC_API_KEY).</p>
        </div>

        <button onClick={handleSave} disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-accent text-background rounded text-xs font-semibold hover:bg-accent-hover disabled:opacity-50">
          <Save size={12} />
          {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}