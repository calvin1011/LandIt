import React, { useState } from 'react';
import { API_BASE } from '../config';

const ScoreRing = ({ score, label, color }) => {
  const circumference = 2 * Math.PI * 36;
  const strokeDashoffset = circumference - ((score / 100) * circumference);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
      <div style={{ position: 'relative', width: '80px', height: '80px' }}>
        <svg width="80" height="80" viewBox="0 0 80 80" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="40" cy="40" r="36" stroke="#374151" strokeWidth="6" fill="transparent" />
          <circle
            cx="40" cy="40" r="36"
            stroke={color}
            strokeWidth="6"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
          />
        </svg>
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)', fontSize: '18px', fontWeight: 'bold', color
        }}>
          {score}
        </div>
      </div>
      <span style={{ fontSize: '12px', fontWeight: '600', color: 'rgba(255,255,255,0.9)' }}>{label}</span>
    </div>
  );
};

const EnhanceAndExportPanel = ({ userEmail }) => {
  const [jobDescription, setJobDescription] = useState('');
  const [enhancing, setEnhancing] = useState(false);
  const [enhanceError, setEnhanceError] = useState('');
  const [enhancement, setEnhancement] = useState(null);
  const [template, setTemplate] = useState('classic');
  const [atsMode, setAtsMode] = useState(false);
  const [downloading, setDownloading] = useState({ pdf: false, docx: false });
  const [lastFilename, setLastFilename] = useState('');
  const [coverLetterModalOpen, setCoverLetterModalOpen] = useState(false);
  const [coverLetterGenerating, setCoverLetterGenerating] = useState(false);
  const [coverLetterError, setCoverLetterError] = useState('');
  const [coverLetterText, setCoverLetterText] = useState('');
  const [coverLetterPayload, setCoverLetterPayload] = useState(null);
  const [coverLetterExporting, setCoverLetterExporting] = useState({ pdf: false, docx: false });

  const handleEnhance = async () => {
    if (!userEmail) return;
    setEnhanceError('');
    setEnhancing(true);
    try {
      const body = { user_email: userEmail };
      if (jobDescription.trim()) body.job_description = jobDescription.trim();
      const res = await fetch(`${API_BASE}/resume/enhance-for-job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setEnhancement(data);
    } catch (e) {
      setEnhanceError(e.message || 'Enhancement failed');
    } finally {
      setEnhancing(false);
    }
  };

  const handleExport = async (format) => {
    if (!userEmail) return;
    const key = format === 'pdf' ? 'pdf' : 'docx';
    setDownloading(prev => ({ ...prev, [key]: true }));
    setLastFilename('');
    try {
      const res = await fetch(`${API_BASE}/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: userEmail,
          template: atsMode ? 'classic' : template,
          ats_mode: atsMode
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Export failed: ${res.status}`);
      }
      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition');
      let filename = `resume.${format}`;
      if (disposition) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) filename = match[1].replace(/['"]/g, '').trim();
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setLastFilename(filename);
    } catch (e) {
      setEnhanceError(e.message || `Export ${format} failed`);
    } finally {
      setDownloading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleOpenCoverLetter = () => {
    setCoverLetterError('');
    setCoverLetterModalOpen(true);
    if (!coverLetterPayload && jobDescription.trim()) {
      setCoverLetterGenerating(true);
      fetch(`${API_BASE}/resume/generate-cover-letter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: userEmail,
          job_description: jobDescription.trim()
        })
      })
        .then(res => {
          if (!res.ok) return res.json().then(d => { throw new Error(d.detail || 'Generate failed'); });
          return res.json();
        })
        .then(data => {
          setCoverLetterText(data.cover_letter_text || '');
          setCoverLetterPayload(data.payload || null);
        })
        .catch(e => setCoverLetterError(e.message || 'Failed to generate cover letter'))
        .finally(() => setCoverLetterGenerating(false));
    } else if (!coverLetterPayload) {
      setCoverLetterError('Paste a job description above and click Enhance, or generate again after adding a JD.');
    }
  };

  const handleCoverLetterExport = async (format) => {
    if (!coverLetterPayload) return;
    const key = format === 'pdf' ? 'pdf' : 'docx';
    setCoverLetterExporting(prev => ({ ...prev, [key]: true }));
    const paragraphs = coverLetterText.trim().split(/\n\n+/).filter(Boolean);
    const payload = {
      ...coverLetterPayload,
      paragraphs: paragraphs.length ? paragraphs : [coverLetterText.trim() || '']
    };
    try {
      const res = await fetch(`${API_BASE}/export/cover-letter-${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Export failed: ${res.status}`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cover-letter.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (e) {
      setCoverLetterError(e.message || `Export ${format} failed`);
    } finally {
      setCoverLetterExporting(prev => ({ ...prev, [key]: false }));
    }
  };

  const atsBefore = enhancement?.ats_analysis?.score_before ?? 0;
  const atsAfter = enhancement?.ats_analysis?.score_after ?? 0;
  const atsDelta = atsAfter - atsBefore;
  const kw = enhancement?.keyword_coverage || { found: [], added: [], missing: [] };
  const jobMatch = enhancement?.job_match_delta || { before: 0, after: 0, delta: 0 };
  const effectiveTemplate = atsMode ? 'classic' : template;

  const sectionStyle = {
    background: 'rgba(255, 255, 255, 0.12)',
    backdropFilter: 'blur(20px)',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '20px',
    border: '1px solid rgba(255,255,255,0.18)',
    boxShadow: '0 8px 32px rgba(31, 38, 135, 0.15)'
  };

  const cardStyle = (selected) => ({
    flex: 1,
    minWidth: '100px',
    padding: '16px',
    borderRadius: '12px',
    border: selected ? '2px solid #6366f1' : '1px solid rgba(255,255,255,0.2)',
    background: selected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255,255,255,0.05)',
    cursor: atsMode && selected ? 'default' : 'pointer',
    color: 'white',
    textAlign: 'center',
    transition: 'all 0.2s ease'
  });

  const renderBullets = (bullets) => (bullets || []).map((b, i) => (
    <li key={i} style={{ marginBottom: '6px', fontSize: '14px' }}>{typeof b === 'string' ? b : b?.text || ''}</li>
  ));

  const renderWorkSection = (resume, side) => {
    const work = resume?.work_experience || [];
    return (
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: 'rgba(255,255,255,0.9)' }}>Work Experience</h4>
        {work.length === 0 ? <p style={{ margin: 0, fontSize: '13px', opacity: 0.8 }}>None</p> : work.map((exp, i) => (
          <div key={i} style={{ marginBottom: '12px', padding: '8px', background: 'rgba(0,0,0,0.1)', borderRadius: '8px' }}>
            <div style={{ fontWeight: '600', fontSize: '13px' }}>{exp.title} at {exp.company}</div>
            <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px' }}>{renderBullets(exp.bullets)}</ul>
          </div>
        ))}
      </div>
    );
  };

  const renderSummary = (text) => (
    <div style={{ marginBottom: '12px' }}>
      <h4 style={{ margin: '0 0 6px 0', fontSize: '14px', color: 'rgba(255,255,255,0.9)' }}>Summary</h4>
      <p style={{ margin: 0, fontSize: '13px', lineHeight: 1.5, opacity: 0.95 }}>{text || 'None'}</p>
    </div>
  );

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={sectionStyle}>
        <h3 style={{ color: 'white', marginTop: 0, marginBottom: '12px', fontSize: '18px' }}>
          Job description (optional but unlocks full enhancement)
        </h3>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description here, then click Enhance to tailor your resume for this role."
          style={{
            width: '100%',
            minHeight: '120px',
            padding: '16px',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.2)',
            fontSize: '14px',
            background: 'rgba(255,255,255,0.08)',
            color: 'white',
            resize: 'vertical',
            boxSizing: 'border-box'
          }}
        />
        <button
          onClick={handleEnhance}
          disabled={enhancing}
          style={{
            marginTop: '12px',
            padding: '12px 24px',
            background: enhancing ? '#6b7280' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            fontWeight: '600',
            cursor: enhancing ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          {enhancing ? 'Enhancing...' : 'Enhance Resume For This Job'}
        </button>
        {enhanceError && (
          <p style={{ color: '#f87171', marginTop: '12px', fontSize: '14px' }}>{enhanceError}</p>
        )}
      </div>

      {enhancement && (
        <>
          <div style={sectionStyle}>
            <h3 style={{ color: 'white', marginTop: 0, marginBottom: '16px', fontSize: '18px' }}>Enhancement results</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px', alignItems: 'flex-start', marginBottom: '20px' }}>
              <ScoreRing score={atsBefore} label="ATS before" color="#94a3b8" />
              <ScoreRing score={atsAfter} label="ATS after" color={atsDelta >= 0 ? '#34d399' : '#f87171'} />
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
                <span style={{ fontSize: '24px', fontWeight: 'bold', color: atsDelta >= 0 ? '#34d399' : '#f87171' }}>
                  {atsDelta >= 0 ? '+' : ''}{atsDelta}
                </span>
                <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>ATS delta</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
                <span style={{ fontSize: '14px', color: 'white' }}>Job match</span>
                <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.9)' }}>
                  {(jobMatch.before * 100).toFixed(0)}% -> {(jobMatch.after * 100).toFixed(0)}%
                  {jobMatch.delta !== 0 && (
                    <span style={{ color: jobMatch.delta > 0 ? '#34d399' : '#f87171', marginLeft: '6px' }}>
                      ({jobMatch.delta > 0 ? '+' : ''}{(jobMatch.delta * 100).toFixed(1)}%)
                    </span>
                  )}
                </span>
              </div>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ color: 'rgba(255,255,255,0.95)', marginBottom: '8px', fontSize: '14px' }}>Keyword coverage</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '13px' }}>
                <span style={{ background: '#166534', color: '#dcfce7', padding: '4px 10px', borderRadius: '8px' }}>
                  Found: {kw.found?.length ?? 0}
                </span>
                <span style={{ background: '#1e40af', color: '#dbeafe', padding: '4px 10px', borderRadius: '8px' }}>
                  Added: {kw.added?.length ?? 0}
                </span>
                <span style={{ background: '#7f1d1d', color: '#fecaca', padding: '4px 10px', borderRadius: '8px' }}>
                  Missing: {kw.missing?.length ?? 0}
                </span>
              </div>
            </div>
            {enhancement.improvements_made?.length > 0 && (
              <div>
                <h4 style={{ color: 'rgba(255,255,255,0.95)', marginBottom: '8px', fontSize: '14px' }}>Improvements made</h4>
                <ul style={{ margin: 0, paddingLeft: '20px', color: 'rgba(255,255,255,0.9)', fontSize: '13px' }}>
                  {enhancement.improvements_made.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div style={sectionStyle}>
            <h3 style={{ color: 'white', marginTop: 0, marginBottom: '16px', fontSize: '18px' }}>Side-by-side comparison</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>
              <div style={{ padding: '16px', background: 'rgba(0,0,0,0.15)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#94a3b8' }}>Original</h4>
                {renderSummary(enhancement.original_resume?.summary)}
                {renderWorkSection(enhancement.original_resume, 'left')}
              </div>
              <div style={{ padding: '16px', background: 'rgba(34, 197, 94, 0.08)', borderRadius: '12px', border: '1px solid rgba(52, 211, 153, 0.3)' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#34d399' }}>Enhanced</h4>
                {renderSummary(enhancement.enhanced_resume?.summary)}
                {renderWorkSection(enhancement.enhanced_resume, 'right')}
              </div>
            </div>
          </div>
        </>
      )}

      <div style={sectionStyle}>
        <h3 style={{ color: 'white', marginTop: 0, marginBottom: '12px', fontSize: '18px' }}>Template</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'rgba(255,255,255,0.95)', fontSize: '14px' }}>
          <input
            type="checkbox"
            checked={atsMode}
            onChange={(e) => setAtsMode(e.target.checked)}
          />
          Force ATS Mode (locks Classic)
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          <div
            style={cardStyle(effectiveTemplate === 'classic')}
            onClick={() => !atsMode && setTemplate('classic')}
          >
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>Classic</div>
            <span style={{ fontSize: '11px', background: '#166534', color: '#dcfce7', padding: '2px 8px', borderRadius: '6px' }}>ATS Safe</span>
          </div>
          <div
            style={cardStyle(effectiveTemplate === 'modern')}
            onClick={() => !atsMode && setTemplate('modern')}
          >
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>Modern</div>
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.8)' }}>Two-column</span>
          </div>
          <div
            style={cardStyle(effectiveTemplate === 'minimal')}
            onClick={() => !atsMode && setTemplate('minimal')}
          >
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>Minimal</div>
            <span style={{ fontSize: '11px', color: '#fbbf24' }}>May Reduce ATS Score</span>
          </div>
        </div>
      </div>

      <div style={sectionStyle}>
        <h3 style={{ color: 'white', marginTop: 0, marginBottom: '16px', fontSize: '18px' }}>Download</h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleExport('pdf')}
            disabled={downloading.pdf}
            style={{
              padding: '12px 24px',
              background: downloading.pdf ? '#6b7280' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: downloading.pdf ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            {downloading.pdf ? 'Generating...' : 'Download PDF'}
          </button>
          <button
            onClick={() => handleExport('docx')}
            disabled={downloading.docx}
            style={{
              padding: '12px 24px',
              background: downloading.docx ? '#6b7280' : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: downloading.docx ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            {downloading.docx ? 'Generating...' : 'Download DOCX'}
          </button>
          <button
            onClick={handleOpenCoverLetter}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Cover Letter
          </button>
        </div>
        {lastFilename && (
          <p style={{ marginTop: '12px', color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>Generated: {lastFilename}</p>
        )}
      </div>

      {coverLetterModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={(e) => e.target === e.currentTarget && setCoverLetterModalOpen(false)}
        >
          <div
            style={{
              background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
              borderRadius: '16px',
              padding: '24px',
              maxWidth: '640px',
              width: '90%',
              maxHeight: '85vh',
              overflow: 'auto',
              border: '1px solid rgba(255,255,255,0.12)',
              boxShadow: '0 25px 50px rgba(0,0,0,0.4)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ color: 'white', margin: 0, fontSize: '18px' }}>Cover Letter</h3>
              <button
                type="button"
                onClick={() => setCoverLetterModalOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: '20px',
                  cursor: 'pointer',
                  padding: '0 4px'
                }}
              >
                x
              </button>
            </div>
            {coverLetterGenerating && (
              <p style={{ color: 'rgba(255,255,255,0.9)', marginBottom: '12px' }}>Generating cover letter...</p>
            )}
            {coverLetterError && (
              <p style={{ color: '#f87171', marginBottom: '12px', fontSize: '14px' }}>{coverLetterError}</p>
            )}
            {(coverLetterPayload || coverLetterText) && (
              <>
                <textarea
                  value={coverLetterText}
                  onChange={(e) => setCoverLetterText(e.target.value)}
                  placeholder="Cover letter body (edit as needed)"
                  style={{
                    width: '100%',
                    minHeight: '200px',
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.2)',
                    fontSize: '14px',
                    background: 'rgba(255,255,255,0.08)',
                    color: 'white',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                    marginBottom: '16px'
                  }}
                />
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => handleCoverLetterExport('pdf')}
                    disabled={coverLetterExporting.pdf}
                    style={{
                      padding: '10px 20px',
                      background: coverLetterExporting.pdf ? '#6b7280' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontWeight: '600',
                      cursor: coverLetterExporting.pdf ? 'not-allowed' : 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {coverLetterExporting.pdf ? 'Generating...' : 'Download PDF'}
                  </button>
                  <button
                    onClick={() => handleCoverLetterExport('docx')}
                    disabled={coverLetterExporting.docx}
                    style={{
                      padding: '10px 20px',
                      background: coverLetterExporting.docx ? '#6b7280' : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontWeight: '600',
                      cursor: coverLetterExporting.docx ? 'not-allowed' : 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {coverLetterExporting.docx ? 'Generating...' : 'Download DOCX'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhanceAndExportPanel;
