"""
app.py — TrustRAG Web Arayüzü
Çalıştırmak için: python app.py
Ardından tarayıcıda: http://localhost:8765
"""

import json
import threading
import time
import http.server
import socketserver
import urllib.parse
from pathlib import Path

PORT = 8765

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrustRAG</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.9/purify.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --void:   #06070B;
    --deep:   #0B1020;
    --elev:   #111827;
    --elev-2: #161C2C;

    --blue:   #1D4ED8;
    --cyan:   #00E5FF;
    --violet: #8B5CF6;
    --aurora: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 55%, var(--violet) 100%);

    --text:     #E8ECF7;
    --text-dim: #9AA3C0;
    --muted:    #5B6280;
    --muted-2:  #333952;

    --border:   rgba(255,255,255,0.07);
    --border-2: rgba(255,255,255,0.14);
    --glass:    rgba(17,24,39,0.55);
    --glass-2:  rgba(17,24,39,0.80);

    --r-lg: 20px;
    --r-md: 14px;
    --r-sm: 10px;

    --font-display: 'Space Grotesk', 'Inter', sans-serif;
    --font-body: 'Inter', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }

  html, body {
    height: 100%;
    background: var(--void);
    color: var(--text);
    font-family: var(--font-body);
    font-size: 15px;
    line-height: 1.6;
    overflow: hidden;
  }

  body {
    background:
      radial-gradient(1100px 750px at 12% -8%, rgba(29,78,216,0.16), transparent 60%),
      radial-gradient(900px 650px at 105% 108%, rgba(139,92,246,0.13), transparent 55%),
      var(--void);
  }

  ::selection { background: rgba(0,229,255,0.25); color: #fff; }

  :focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: 2px;
    border-radius: 4px;
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.001ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.001ms !important;
      scroll-behavior: auto !important;
    }
  }

  /* ── AMBIENT BACKGROUND ── */
  .ambient {
    position: fixed; inset: 0;
    overflow: hidden;
    z-index: 0;
    pointer-events: none;
  }
  .ambient span {
    position: absolute;
    border-radius: 50%;
    filter: blur(130px);
    opacity: 0.32;
    mix-blend-mode: screen;
    will-change: transform;
  }
  .ambient .b1 {
    width: 560px; height: 560px;
    background: var(--cyan);
    top: -180px; left: -120px;
    animation: float1 24s ease-in-out infinite alternate;
  }
  .ambient .b2 {
    width: 520px; height: 520px;
    background: var(--blue);
    bottom: -220px; right: -140px;
    animation: float2 28s ease-in-out infinite alternate;
  }
  .ambient .b3 {
    width: 440px; height: 440px;
    background: var(--violet);
    top: 38%; left: 52%;
    animation: float3 21s ease-in-out infinite alternate;
    opacity: 0.22;
  }
  @keyframes float1 { 0%{ transform:translate(0,0) scale(1); } 100%{ transform:translate(90px,70px) scale(1.18); } }
  @keyframes float2 { 0%{ transform:translate(0,0) scale(1); } 100%{ transform:translate(-80px,-50px) scale(1.12); } }
  @keyframes float3 { 0%{ transform:translate(0,0) scale(1); } 100%{ transform:translate(-60px,80px) scale(0.88); } }

  .noise {
    position: fixed; inset: 0;
    z-index: 1;
    opacity: 0.035;
    pointer-events: none;
    mix-blend-mode: overlay;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  }

  /* ── LAYOUT ── */
  .layout {
    display: flex;
    height: 100vh;
    position: relative;
    z-index: 2;
    opacity: 0;
    animation: pageIn 0.6s ease 0.05s forwards;
  }
  @keyframes pageIn { to { opacity: 1; } }

  .scrim {
    display: none;
    position: fixed; inset: 0;
    background: rgba(6,7,11,0.6);
    backdrop-filter: blur(2px);
    z-index: 9;
  }

  /* ── SIDEBAR ── */
  .sidebar {
    width: 280px;
    flex-shrink: 0;
    background: linear-gradient(180deg, rgba(17,24,39,0.62), rgba(11,16,32,0.62));
    backdrop-filter: blur(26px);
    -webkit-backdrop-filter: blur(26px);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 22px 16px 16px;
    overflow-y: auto;
    z-index: 10;
    transition: transform 0.28s ease;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 22px;
    padding: 0 4px;
  }

  .logo-text { line-height: 1.25; }
  .logo-name { font-family: var(--font-display); font-size: 16px; font-weight: 600; color: #F3F6FF; letter-spacing: -0.2px; }
  .logo-sub  { font-size: 10px; color: var(--muted); letter-spacing: 0.8px; text-transform: uppercase; }

  /* nav */
  .nav { display: flex; flex-direction: column; gap: 2px; margin-bottom: 18px; }
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 10px;
    border-radius: 9px;
    font-size: 13px;
    color: var(--muted);
    cursor: pointer;
    position: relative;
    transition: background 0.15s, color 0.15s;
    background: none; border: none; width: 100%; text-align: left;
    font-family: var(--font-body);
  }
  .nav-item .nav-ic { width: 16px; text-align: center; font-size: 13px; }
  .nav-item.active { background: rgba(255,255,255,0.05); color: var(--text); }
  .nav-item.active::before {
    content: '';
    position: absolute; left: -16px; top: 50%; transform: translateY(-50%);
    width: 3px; height: 16px; border-radius: 3px;
    background: var(--aurora);
  }
  .nav-item:not(.active):hover { background: rgba(255,255,255,0.03); color: var(--text-dim); }
  .nav-soon {
    margin-left: auto;
    font-size: 8px; padding: 2px 6px;
    border-radius: 20px;
    background: rgba(255,255,255,0.05);
    color: var(--muted-2);
    letter-spacing: 0.5px; text-transform: uppercase;
    font-family: var(--font-mono);
  }

  .sb-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: var(--muted-2);
    margin-bottom: 8px;
    margin-top: 18px;
    padding: 0 2px;
  }

  .divider { height: 1px; background: var(--border); margin: 14px 0; }

  /* status card */
  .status-card {
    display: flex; align-items: center; gap: 10px;
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 10px 12px;
    backdrop-filter: blur(14px);
  }
  .led {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--cyan);
    box-shadow: 0 0 8px var(--cyan);
    animation: breathe 2.8s ease-in-out infinite;
    flex-shrink: 0;
  }
  @keyframes breathe { 0%,100% { opacity:1; } 50% { opacity:0.35; } }
  .status-col { line-height: 1.35; min-width: 0; }
  .status-text { font-size: 12px; color: var(--text-dim); font-weight: 500; }
  .status-sub { font-size: 10.5px; color: var(--muted-2); font-family: var(--font-mono); }

  /* stat grids */
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .stat-card {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    padding: 9px 11px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .stat-card:hover { border-color: var(--border-2); transform: translateY(-1px); }
  .stat-num { font-size: 17px; font-weight: 600; font-family: var(--font-mono); color: var(--cyan); line-height: 1.15; }
  .stat-num.dim { color: var(--muted-2); }
  .stat-lbl { font-size: 9px; color: var(--muted-2); text-transform: uppercase; letter-spacing: 0.7px; margin-top: 4px; }

  /* model rows */
  .model-row { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; margin-bottom: 2px; }
  .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .dot-cyan { background: var(--cyan); box-shadow: 0 0 5px var(--cyan); }
  .dot-violet { background: var(--violet); box-shadow: 0 0 5px var(--violet); }
  .model-name { font-size: 11.5px; font-family: var(--font-mono); color: #7C84A6; flex: 1; }
  .model-tag { font-size: 9px; color: var(--muted-2); text-transform: uppercase; letter-spacing: 0.5px; }

  .sb-bottom { margin-top: auto; }
  .clear-btn {
    width: 100%;
    padding: 9px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    color: var(--muted-2);
    font-size: 12px;
    font-family: var(--font-body);
    cursor: pointer;
    transition: all 0.18s;
  }
  .clear-btn:hover { border-color: rgba(239,68,68,0.32); color: #F87171; background: rgba(239,68,68,0.05); }

  /* ── MAIN ── */
  .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; min-width: 0; }

  .hamburger {
    display: none;
    width: 32px; height: 32px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--glass);
    color: var(--text-dim);
    align-items: center; justify-content: center;
    cursor: pointer;
    font-size: 14px;
  }

  .topbar {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 15px 26px;
    border-bottom: 1px solid var(--border);
    background: rgba(8,10,17,0.35);
    backdrop-filter: blur(18px);
    flex-shrink: 0;
  }
  .topbar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .topbar-title { font-family: var(--font-display); font-size: 13.5px; font-weight: 500; color: #B8BFDA; white-space: nowrap; }
  .topbar-badge {
    font-size: 10px; padding: 3px 10px; border-radius: 20px;
    background: rgba(0,229,255,0.07);
    border: 1px solid rgba(0,229,255,0.16);
    color: var(--cyan);
    font-weight: 500; letter-spacing: 0.3px;
    white-space: nowrap;
  }
  .topbar-ver { font-size: 11px; font-family: var(--font-mono); color: var(--muted-2); }

  /* ── MESSAGES ── */
  .messages { flex: 1; overflow-y: auto; padding: 30px 26px 10px; scroll-behavior: smooth; }
  .messages::-webkit-scrollbar { width: 5px; }
  .messages::-webkit-scrollbar-track { background: transparent; }
  .messages::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.14); border-radius: 10px; transition: background 0.2s; }
  .messages::-webkit-scrollbar-thumb:hover { background: rgba(0,229,255,0.4); }
  .messages { scrollbar-width: thin; scrollbar-color: rgba(0,229,255,0.2) transparent; }

  .msg-wrap { max-width: 860px; margin: 0 auto; }

  @keyframes riseIn {
    from { opacity: 0; transform: translateY(10px); filter: blur(6px); }
    to   { opacity: 1; transform: translateY(0); filter: blur(0); }
  }

  .msg-user { display: flex; justify-content: flex-end; margin: 14px 0; animation: riseIn 0.45s cubic-bezier(.16,.8,.24,1) both; }
  .bubble-user {
    max-width: 68%;
    background: var(--glass);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(59,142,234,0.16);
    border-radius: var(--r-lg);
    padding: 12px 17px;
    color: #D2D7EC;
    font-size: 14.5px;
    line-height: 1.7;
  }

  .msg-ai { display: flex; gap: 13px; align-items: flex-start; margin: 18px 0; animation: riseIn 0.45s cubic-bezier(.16,.8,.24,1) both; }
  .ai-col { min-width: 0; flex: 1; max-width: 78%; }

  .msg-meta-top {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    font-size: 10.5px; font-family: var(--font-mono);
    color: var(--muted-2);
    margin: 0 0 7px 2px;
  }
  .msg-meta-top .sep { opacity: 0.4; }
  .msg-meta-top .hi { color: var(--cyan); opacity: 0.75; }

  .bubble-wrap { padding: 1px; border-radius: 21px; background: linear-gradient(135deg, rgba(0,229,255,0.32), rgba(29,78,216,0.22), rgba(139,92,246,0.28)); }
  .bubble-ai {
    background: var(--glass-2);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
    border-radius: 20px;
    padding: 15px 18px;
    color: #C2C8E0;
    font-size: 14.5px;
    line-height: 1.78;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 10px 26px -14px rgba(0,0,0,0.6);
    position: relative;
  }
  .bubble-ai p { margin: 0 0 10px; }
  .bubble-ai p:last-child { margin-bottom: 0; }
  .bubble-ai ul, .bubble-ai ol { margin: 0 0 10px 20px; }
  .bubble-ai pre {
    background: #0A0D14; border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; overflow-x: auto; margin: 10px 0;
    font-family: var(--font-mono); font-size: 12.5px;
  }
  .bubble-ai code { font-family: var(--font-mono); font-size: 0.9em; background: rgba(255,255,255,0.07); padding: 1px 5px; border-radius: 5px; }
  .bubble-ai pre code { background: none; padding: 0; }
  .bubble-ai blockquote { border-left: 2px solid var(--cyan); padding: 3px 0 3px 12px; margin: 8px 0; color: var(--text-dim); font-style: italic; }
  .bubble-ai table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; }
  .bubble-ai th, .bubble-ai td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  .bubble-ai th { background: rgba(255,255,255,0.04); font-family: var(--font-mono); font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-dim); }
  .bubble-ai a { color: var(--cyan); text-decoration: none; border-bottom: 1px solid rgba(0,229,255,0.3); }
  .bubble-ai a:hover { border-color: var(--cyan); }

  .type-cursor { display: inline-block; width: 2px; height: 14px; background: var(--cyan); margin-left: 1px; vertical-align: -2px; animation: blink 0.9s step-start infinite; }
  @keyframes blink { 50% { opacity: 0; } }

  /* thinking */
  .thinking { display: flex; flex-direction: column; gap: 8px; padding: 2px 1px; }
  .think-line { display: flex; align-items: center; gap: 9px; font-size: 12.5px; color: var(--muted); opacity: 0.38; transition: opacity 0.3s, color 0.3s; }
  .think-line.active { opacity: 1; color: var(--text-dim); }
  .think-line.done { opacity: 0.55; color: var(--cyan); }
  .think-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
  .think-line.active .think-dot { animation: pulseDot 1s ease-in-out infinite; }
  @keyframes pulseDot { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.6); opacity: 0.5; } }

  /* sources */
  .sources { display: flex; flex-direction: column; gap: 6px; margin-top: 13px; padding-top: 12px; border-top: 1px solid var(--border); }
  .source-card {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 11px;
    border-radius: var(--r-sm);
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    cursor: pointer;
    transition: transform 0.18s, background 0.18s, border-color 0.18s, box-shadow 0.18s;
  }
  .source-card:hover {
    transform: translateY(-2px) scale(1.01);
    background: rgba(255,255,255,0.045);
    border-color: rgba(0,229,255,0.28);
    box-shadow: 0 12px 22px -14px rgba(0,229,255,0.3);
  }
  .source-icon {
    width: 26px; height: 26px; flex-shrink: 0;
    border-radius: 7px;
    background: linear-gradient(135deg, rgba(0,229,255,0.16), rgba(139,92,246,0.16));
    border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px;
  }
  .source-info { min-width: 0; flex: 1; }
  .source-name { font-size: 12.5px; color: var(--text-dim); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .source-sub { font-size: 10.5px; color: var(--muted-2); font-family: var(--font-mono); margin-top: 1px; }
  .source-score {
    font-size: 10px; font-family: var(--font-mono);
    padding: 2px 8px; border-radius: 20px; flex-shrink: 0;
    background: rgba(0,229,255,0.08); color: var(--cyan); border: 1px solid rgba(0,229,255,0.18);
  }
  .source-score.mid { background: rgba(29,78,216,0.1); color: #7BA3F5; border-color: rgba(29,78,216,0.22); }
  .source-score.low { background: rgba(255,255,255,0.04); color: var(--muted); border-color: var(--border); }
  .source-arrow { font-size: 12px; color: var(--muted-2); flex-shrink: 0; transition: transform 0.18s, color 0.18s; }
  .source-card:hover .source-arrow { transform: translateX(2px); color: var(--cyan); }

  /* orb (signature element) */
  .orb { position: relative; width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0; margin-top: 1px; }
  .orb-lg { width: 84px; height: 84px; margin: 0 auto; }
  .orb::before, .orb::after {
    content: ''; position: absolute; inset: 0; border-radius: 50%;
    background: conic-gradient(from 0deg, var(--cyan), var(--blue), var(--violet), var(--cyan));
  }
  .orb::before { filter: blur(10px); opacity: 0.65; animation: orbSpin 7s linear infinite, orbPulse 3.2s ease-in-out infinite; }
  .orb::after { opacity: 0.95; animation: orbSpin 7s linear infinite reverse; }
  .orb.active::before { animation: orbSpin 2.6s linear infinite, orbPulse 1s ease-in-out infinite; }
  .orb-lg::before { filter: blur(26px); }
  .orb-glyph {
    position: absolute; inset: 0; z-index: 2;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; color: #060A12;
  }
  .orb-lg .orb-glyph { font-size: 34px; }
  @keyframes orbSpin { to { transform: rotate(360deg); } }
  @keyframes orbPulse { 0%,100% { transform: scale(1); opacity: 0.65; } 50% { transform: scale(1.14); opacity: 0.38; } }

  /* ── EMPTY STATE ── */
  .empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding-bottom: 50px; text-align: center; }
  .empty-title { font-family: var(--font-display); font-size: 27px; font-weight: 600; letter-spacing: -0.4px; margin: 20px 0 4px; background: var(--aurora); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .empty-eyebrow { font-size: 10.5px; letter-spacing: 1.6px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
  .empty-sub { font-size: 13px; color: var(--muted); line-height: 1.65; max-width: 340px; margin-top: 2px; }

  .sug-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 30px; width: 420px; max-width: 90vw; }
  .sug-card {
    text-align: left; padding: 15px 16px;
    background: var(--glass);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    cursor: pointer;
    transition: transform 0.18s, border-color 0.18s, box-shadow 0.18s, background 0.18s;
    font-family: var(--font-body);
  }
  .sug-card:hover { transform: translateY(-3px) scale(1.012); border-color: rgba(0,229,255,0.28); background: rgba(255,255,255,0.045); box-shadow: 0 16px 30px -18px rgba(0,229,255,0.35); }
  .sug-ic { font-size: 18px; margin-bottom: 8px; }
  .sug-title { font-size: 13px; font-weight: 600; color: var(--text-dim); }
  .sug-desc { font-size: 11px; color: var(--muted-2); margin-top: 3px; }

  /* ── INPUT AREA ── */
  .input-area { padding: 14px 26px 20px; flex-shrink: 0; }
  .input-wrap { max-width: 860px; margin: 0 auto; }

  .input-outer {
    padding: 1.5px;
    border-radius: 21px;
    background: linear-gradient(120deg, rgba(0,229,255,0.45), rgba(29,78,216,0.35), rgba(139,92,246,0.45), rgba(0,229,255,0.45));
    background-size: 250% 250%;
    animation: borderFlow 9s ease infinite;
  }
  @keyframes borderFlow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

  .input-inner {
    border-radius: 19.5px;
    background: var(--glass-2);
    backdrop-filter: blur(26px);
    -webkit-backdrop-filter: blur(26px);
    padding: 12px 14px 10px;
  }

  .input-top { display: flex; align-items: flex-start; gap: 10px; }
  .icon-btn {
    width: 30px; height: 30px; flex-shrink: 0;
    border-radius: 9px;
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
    color: var(--muted);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 13.5px;
    transition: all 0.16s;
  }
  .icon-btn:hover { border-color: var(--border-2); color: var(--text-dim); background: rgba(255,255,255,0.05); transform: translateY(-1px); }

  #query {
    flex: 1; background: transparent; border: none; outline: none;
    color: var(--text); font-family: var(--font-body); font-size: 14.5px; line-height: 1.6;
    resize: none; min-height: 24px; max-height: 140px; padding: 4px 0;
  }
  #query::placeholder { color: var(--muted-2); }

  .input-bottom { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
  .mode-pill {
    display: flex; align-items: center; gap: 6px;
    padding: 5px 11px; border-radius: 20px;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    font-size: 11.5px; color: var(--muted);
    cursor: pointer; transition: all 0.18s;
    font-family: var(--font-body);
  }
  .mode-pill.on { background: linear-gradient(120deg, rgba(0,229,255,0.16), rgba(139,92,246,0.16)); border-color: rgba(0,229,255,0.36); color: var(--text); }
  .spacer { flex: 1; }

  .send-btn {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--aurora);
    border: none; cursor: pointer; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.15s, box-shadow 0.2s, opacity 0.15s;
  }
  .send-btn:hover:not(:disabled) { transform: rotate(-8deg) scale(1.07); box-shadow: 0 0 22px rgba(0,229,255,0.4); }
  .send-btn:active:not(:disabled) { transform: scale(0.92); }
  .send-btn:disabled { opacity: 0.3; cursor: default; }
  .send-btn svg { transform-box: fill-box; transform-origin: center; }
  .spin { animation: spin 0.85s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .input-hint { text-align: center; font-size: 10px; color: #181C28; margin-top: 10px; letter-spacing: 0.3px; }

  /* toast */
  .toast-root { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 999; display: flex; flex-direction: column; gap: 8px; align-items: center; pointer-events: none; }
  .toast {
    padding: 9px 16px; border-radius: 20px;
    background: rgba(17,24,39,0.92); backdrop-filter: blur(14px);
    border: 1px solid var(--border-2);
    font-size: 12.5px; color: var(--text-dim);
    box-shadow: 0 14px 28px -14px rgba(0,0,0,0.6);
    opacity: 0; transform: translateY(8px);
    transition: opacity 0.25s, transform 0.25s;
  }
  .toast.show { opacity: 1; transform: translateY(0); }

  /* ── RESPONSIVE ── */
  @media (max-width: 880px) {
    .hamburger { display: flex; }
    .sidebar { position: fixed; inset: 0 auto 0 0; transform: translateX(-100%); box-shadow: 20px 0 40px rgba(0,0,0,0.4); }
    .layout.nav-open .sidebar { transform: translateX(0); }
    .layout.nav-open .scrim { display: block; }
    .bubble-user { max-width: 84%; }
    .ai-col { max-width: 88%; }
    .sug-grid { grid-template-columns: 1fr; width: 320px; }
    .topbar-ver { display: none; }
  }
</style>
</head>
<body>

<div class="ambient"><span class="b1"></span><span class="b2"></span><span class="b3"></span></div>
<div class="noise"></div>
<div class="scrim" id="scrim" onclick="closeNav()"></div>

<div class="layout" id="layout">

  <!-- SIDEBAR -->
  <aside class="sidebar" id="sidebar">
    <div class="logo">
      <div class="orb"><span class="orb-glyph">⬡</span></div>
      <div class="logo-text">
        <div class="logo-name">TrustRAG</div>
        <div class="logo-sub">Local · Private</div>
      </div>
    </div>

    <nav class="nav">
      <button class="nav-item active" type="button"><span class="nav-ic">💬</span>Sohbetler</button>
      <button class="nav-item" type="button" onclick="toast('Belge yönetimi yakında')"><span class="nav-ic">📚</span>Belgeler<span class="nav-soon">yakında</span></button>
      <button class="nav-item" type="button" onclick="toast('Model yönetimi yakında')"><span class="nav-ic">⚡</span>Modeller<span class="nav-soon">yakında</span></button>
      <button class="nav-item" type="button" onclick="toast('Kullanım paneli yakında')"><span class="nav-ic">📈</span>Kullanım<span class="nav-soon">yakında</span></button>
      <button class="nav-item" type="button" onclick="toast('Ayarlar yakında')"><span class="nav-ic">⚙</span>Ayarlar<span class="nav-soon">yakında</span></button>
    </nav>

    <div class="sb-label">Durum</div>
    <div class="status-card">
      <div class="led" id="led"></div>
      <div class="status-col">
        <div class="status-text" id="status-text">Bağlanıyor…</div>
        <div class="status-sub">phi-3.5-mini · yerel</div>
      </div>
    </div>

    <div class="sb-label">Sistem</div>
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num dim" id="sys-latency">—</div><div class="stat-lbl">Gecikme</div></div>
      <div class="stat-card"><div class="stat-num dim" id="sys-speed">—</div><div class="stat-lbl">Hız</div></div>
      <div class="stat-card"><div class="stat-num dim" id="sys-cpu">—</div><div class="stat-lbl">CPU</div></div>
      <div class="stat-card"><div class="stat-num dim" id="sys-ram">—</div><div class="stat-lbl">Bellek</div></div>
    </div>

    <div class="sb-label">Aktif Modeller</div>
    <div class="model-row">
      <div class="dot dot-cyan"></div>
      <div class="model-name">phi-3.5-mini</div>
      <div class="model-tag">chat</div>
    </div>
    <div class="model-row">
      <div class="dot dot-violet"></div>
      <div class="model-name">qwen3-embed</div>
      <div class="model-tag">embed</div>
    </div>

    <div class="divider"></div>

    <div class="sb-label" style="margin-top:0;">Oturum</div>
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num" id="stat-q">0</div><div class="stat-lbl">Sorgu</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-t">0.0s</div><div class="stat-lbl">Ort. Süre</div></div>
    </div>

    <div class="sb-bottom">
      <div class="divider"></div>
      <button class="clear-btn" onclick="clearChat()">Sohbeti Temizle</button>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">
    <div class="topbar">
      <div class="topbar-left">
        <button class="hamburger" onclick="openNav()" aria-label="Menü">☰</button>
        <span class="topbar-title">Belge Asistanı</span>
        <span class="topbar-badge">RAG · Yerel</span>
      </div>
      <span class="topbar-ver">TrustRAG v0.2</span>
    </div>

    <div class="messages" id="messages">
      <div class="msg-wrap">
        <div class="empty" id="empty-state">
          <div class="orb orb-lg"><span class="orb-glyph">⬡</span></div>
          <div class="empty-eyebrow">Private AI Assistant</div>
          <div class="empty-title">TrustRAG</div>
          <div class="empty-sub">Yüklediğiniz belgeler hakkında soru sorun. Tüm yanıtlar yalnızca bu belgelerden üretilir.</div>
          <div class="sug-grid">
            <button class="sug-card" onclick="fillQuery('Bu belgeyi özetle')">
              <div class="sug-ic">📄</div><div class="sug-title">Özetle</div><div class="sug-desc">Uzun metni kısalt</div>
            </button>
            <button class="sug-card" onclick="fillQuery('Bu belgedeki ana kavramı açıkla')">
              <div class="sug-ic">🧠</div><div class="sug-title">Açıkla</div><div class="sug-desc">Kavramları sadeleştir</div>
            </button>
            <button class="sug-card" onclick="fillQuery('İletişim bilgilerini bul')">
              <div class="sug-ic">🔍</div><div class="sug-title">Ara</div><div class="sug-desc">Belirli bilgiyi bul</div>
            </button>
            <button class="sug-card" onclick="fillQuery('Belgedeki farklı bölümleri karşılaştır')">
              <div class="sug-ic">⚡</div><div class="sug-title">Karşılaştır</div><div class="sug-desc">Bölümleri kıyasla</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrap">
        <div class="input-outer">
          <div class="input-inner">
            <div class="input-top">
              <button class="icon-btn" onclick="toast('Dosya ekleme yakında aktif olacak')" title="Dosya ekle">📎</button>
              <textarea id="query" rows="1" placeholder="Belgeleriniz hakkında bir soru sorun…"></textarea>
            </div>
            <div class="input-bottom">
              <button class="mode-pill" id="deep-toggle" onclick="toggleDeep()">⚡ Deep Search</button>
              <div class="spacer"></div>
              <button class="icon-btn" onclick="toast('İnternet modu yakında aktif olacak')" title="İnternet modu">🌐</button>
              <button class="icon-btn" onclick="toast('Sesli giriş yakında aktif olacak')" title="Sesli giriş">🎤</button>
              <button class="send-btn" id="send-btn" onclick="sendQuery()" title="Gönder" aria-label="Gönder">
                <svg id="send-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#060A12" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
                <svg id="send-spinner" class="spin" width="15" height="15" viewBox="0 0 24 24" style="display:none"><circle cx="12" cy="12" r="9" fill="none" stroke="#060A12" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="40 100"></circle></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="input-hint">Tüm veriler cihazınızda işlenir · İnternet bağlantısı gerekmez</div>
      </div>
    </div>
  </main>
</div>

<div class="toast-root" id="toast-root"></div>

<script>
  let queryCount = 0;
  let totalTime = 0;
  let deepSearch = false;

  const msgBox = document.getElementById('messages');
  const queryInput = document.getElementById('query');
  const sendBtn = document.getElementById('send-btn');
  const sendIcon = document.getElementById('send-icon');
  const sendSpinner = document.getElementById('send-spinner');
  const layoutEl = document.getElementById('layout');

  if (window.marked) marked.setOptions({ gfm: true, breaks: true });

  const EMPTY_STATE_HTML = `<div class="empty" id="empty-state">
    <div class="orb orb-lg"><span class="orb-glyph">⬡</span></div>
    <div class="empty-eyebrow">Private AI Assistant</div>
    <div class="empty-title">TrustRAG</div>
    <div class="empty-sub">Yüklediğiniz belgeler hakkında soru sorun. Tüm yanıtlar yalnızca bu belgelerden üretilir.</div>
    <div class="sug-grid">
      <button class="sug-card" onclick="fillQuery('Bu belgeyi özetle')"><div class="sug-ic">📄</div><div class="sug-title">Özetle</div><div class="sug-desc">Uzun metni kısalt</div></button>
      <button class="sug-card" onclick="fillQuery('Bu belgedeki ana kavramı açıkla')"><div class="sug-ic">🧠</div><div class="sug-title">Açıkla</div><div class="sug-desc">Kavramları sadeleştir</div></button>
      <button class="sug-card" onclick="fillQuery('İletişim bilgilerini bul')"><div class="sug-ic">🔍</div><div class="sug-title">Ara</div><div class="sug-desc">Belirli bilgiyi bul</div></button>
      <button class="sug-card" onclick="fillQuery('Belgedeki farklı bölümleri karşılaştır')"><div class="sug-ic">⚡</div><div class="sug-title">Karşılaştır</div><div class="sug-desc">Bölümleri kıyasla</div></button>
    </div>
  </div>`;

  /* ── nav / mobile drawer ── */
  function openNav() { layoutEl.classList.add('nav-open'); }
  function closeNav() { layoutEl.classList.remove('nav-open'); }

  /* ── toast ── */
  function toast(msg) {
    const root = document.getElementById('toast-root');
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    root.appendChild(el);
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 2200);
  }

  function toggleDeep() {
    deepSearch = !deepSearch;
    const btn = document.getElementById('deep-toggle');
    btn.classList.toggle('on', deepSearch);
    if (deepSearch) toast('Deep Search modu yakında aktif olacak');
  }

  /* ── textarea ── */
  queryInput.addEventListener('input', () => {
    queryInput.style.height = 'auto';
    queryInput.style.height = Math.min(queryInput.scrollHeight, 140) + 'px';
    sendBtn.disabled = queryInput.value.trim().length === 0;
  });
  queryInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(); }
  });
  sendBtn.disabled = true;

  function fillQuery(text) {
    queryInput.value = text;
    queryInput.dispatchEvent(new Event('input'));
    queryInput.focus();
    closeNav();
  }

  function clearChat() {
    queryCount = 0; totalTime = 0;
    document.getElementById('stat-q').textContent = '0';
    document.getElementById('stat-t').textContent = '0.0s';
    document.querySelector('.msg-wrap').innerHTML = EMPTY_STATE_HTML;
  }

  function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }

  function scrollBottom() { msgBox.scrollTop = msgBox.scrollHeight; }

  function addUserMsg(text) {
    const empty = document.getElementById('empty-state');
    if (empty) empty.remove();
    const wrap = document.querySelector('.msg-wrap');
    const div = document.createElement('div');
    div.className = 'msg-user';
    div.innerHTML = `<div class="bubble-user">${escHtml(text)}</div>`;
    wrap.appendChild(div);
    scrollBottom();
  }

  function addAIThinking() {
    const wrap = document.querySelector('.msg-wrap');
    const div = document.createElement('div');
    div.className = 'msg-ai';
    div.innerHTML = `
      <div class="orb active"><span class="orb-glyph">⬡</span></div>
      <div class="ai-col">
        <div class="bubble-wrap">
          <div class="bubble-ai">
            <div class="thinking">
              <div class="think-line" data-step="0"><span class="think-dot"></span>Kaynaklar taranıyor</div>
              <div class="think-line" data-step="1"><span class="think-dot"></span>Bağlam analiz ediliyor</div>
              <div class="think-line" data-step="2"><span class="think-dot"></span>Yanıt oluşturuluyor</div>
            </div>
          </div>
        </div>
      </div>`;
    wrap.appendChild(div);
    scrollBottom();

    const lines = div.querySelectorAll('.think-line');
    let i = 0;
    lines[0].classList.add('active');
    div._thinkInterval = setInterval(() => {
      lines.forEach(l => l.classList.remove('active'));
      lines[i].classList.add('done');
      i = (i + 1) % lines.length;
      lines[i].classList.add('active');
      scrollBottom();
    }, 550);

    return div;
  }

  function sourceScoreClass(sim) {
    if (sim >= 0.85) return '';
    if (sim >= 0.65) return 'mid';
    return 'low';
  }

  function buildSourcesHtml(sources) {
    if (!sources || !sources.length) return '';
    const cards = sources.map(s => {
      const pct = Math.round(s.similarity * 100);
      return `<div class="source-card" onclick="toast('Kaynak görüntüleme yakında aktif olacak')">
        <div class="source-icon">📄</div>
        <div class="source-info">
          <div class="source-name">${escHtml(s.source)}</div>
          <div class="source-sub">Belge kaynağı</div>
        </div>
        <div class="source-score ${sourceScoreClass(s.similarity)}">%${pct}</div>
        <div class="source-arrow">→</div>
      </div>`;
    }).join('');
    return `<div class="sources">${cards}</div>`;
  }

  async function streamAnswer(container, answer, sources, latency) {
    clearInterval(container._thinkInterval);
    const bubble = container.querySelector('.bubble-ai');
    const orb = container.querySelector('.orb');
    const aiCol = container.querySelector('.ai-col');
    const bubbleWrap = container.querySelector('.bubble-wrap');

    container.querySelectorAll('.think-line').forEach(l => { l.classList.remove('active'); l.classList.add('done'); });
    await new Promise(r => setTimeout(r, 220));

    bubble.innerHTML = `<span class="type-target"></span><span class="type-cursor"></span>`;
    const target = bubble.querySelector('.type-target');
    const cursor = bubble.querySelector('.type-cursor');

    const totalMs = Math.max(280, Math.min(2200, answer.length * 9));
    const stepMs = Math.max(4, totalMs / Math.max(answer.length, 1));
    let idx = 0;
    await new Promise(resolve => {
      const tick = () => {
        idx += Math.max(1, Math.round(answer.length / (totalMs / 16)));
        target.textContent = answer.slice(0, idx);
        scrollBottom();
        if (idx >= answer.length) { resolve(); return; }
        setTimeout(tick, stepMs);
      };
      tick();
    });
    cursor.remove();
    await new Promise(r => setTimeout(r, 120));

    let html = answer;
    try {
      html = window.marked ? marked.parse(answer) : escHtml(answer);
      if (window.DOMPurify) html = DOMPurify.sanitize(html);
    } catch (e) { html = escHtml(answer); }

    bubble.innerHTML = html + buildSourcesHtml(sources);
    bubble.querySelectorAll('pre code').forEach(block => {
      try { hljs.highlightElement(block); } catch (e) {}
    });
    bubble.querySelectorAll('.source-card').forEach((card, i) => {
      const s = sources[i];
      card.onclick = () => toast('Kaynak görüntüleme yakında aktif olacak');
    });

    if (orb) orb.classList.remove('active');

    const metaTop = document.createElement('div');
    metaTop.className = 'msg-meta-top';
    let metaParts = [];
    if (sources && sources.length) {
      const avg = sources.reduce((a, s) => a + s.similarity, 0) / sources.length;
      metaParts.push(`✨ ${sources.length} belgeden alındı`);
      metaParts.push(`<span class="hi">Güven %${Math.round(avg * 100)}</span>`);
    }
    metaParts.push(`${latency.toFixed(2)}s`);
    metaTop.innerHTML = metaParts.join(' <span class="sep">·</span> ');
    aiCol.insertBefore(metaTop, bubbleWrap);

    scrollBottom();
  }

  function showError(container, message) {
    clearInterval(container._thinkInterval);
    const bubble = container.querySelector('.bubble-ai');
    const orb = container.querySelector('.orb');
    bubble.innerHTML = `⚠️ ${escHtml(message)}`;
    if (orb) orb.classList.remove('active');
    scrollBottom();
  }

  async function sendQuery() {
    const q = queryInput.value.trim();
    if (!q) return;
    queryInput.value = '';
    queryInput.style.height = 'auto';
    sendBtn.disabled = true;
    sendIcon.style.display = 'none';
    sendSpinner.style.display = 'block';

    addUserMsg(q);
    const aiEl = addAIThinking();
    const t0 = Date.now();

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, deep_search: deepSearch })
      });
      const data = await res.json();
      const elapsed = (typeof data.latency === 'number' && data.latency > 0) ? data.latency : (Date.now() - t0) / 1000;

      await streamAnswer(aiEl, data.answer, data.sources || [], elapsed);

      queryCount++;
      totalTime += elapsed;
      document.getElementById('stat-q').textContent = queryCount;
      document.getElementById('stat-t').textContent = (totalTime / queryCount).toFixed(1) + 's';

      const words = (data.answer || '').split(/\s+/).filter(Boolean).length;
      document.getElementById('sys-latency').textContent = elapsed.toFixed(2) + 's';
      document.getElementById('sys-latency').classList.remove('dim');
      document.getElementById('sys-speed').textContent = '≈' + Math.round(words / Math.max(elapsed, 0.01)) + '/s';
      document.getElementById('sys-speed').classList.remove('dim');

    } catch (e) {
      showError(aiEl, 'Sunucu hatası: ' + e.message);
    }

    sendIcon.style.display = 'block';
    sendSpinner.style.display = 'none';
    sendBtn.disabled = queryInput.value.trim().length === 0;
    queryInput.focus();
  }

  /* ── status / system polling ── */
  async function checkStatus() {
    try {
      const r = await fetch('/api/status');
      const d = await r.json();
      const led = document.getElementById('led');
      const st = document.getElementById('status-text');
      if (d.ok) {
        led.style.background = '#00E5FF';
        led.style.boxShadow = '0 0 8px #00E5FF';
        led.style.animation = 'breathe 2.8s ease-in-out infinite';
        st.textContent = 'Yerel AI çalışıyor';
      } else {
        led.style.background = '#EF4444';
        led.style.boxShadow = 'none';
        led.style.animation = 'none';
        st.textContent = 'Model bağlantısı yok';
      }
    } catch { }
  }

  async function pollSystem() {
    try {
      const r = await fetch('/api/system');
      const d = await r.json();
      const cpu = document.getElementById('sys-cpu');
      const ram = document.getElementById('sys-ram');
      if (d.ok) {
        cpu.textContent = Math.round(d.cpu_percent) + '%';
        cpu.classList.remove('dim');
        ram.textContent = Math.round(d.ram_percent) + '%';
        ram.classList.remove('dim');
      } else {
        cpu.textContent = '—'; cpu.classList.add('dim');
        ram.textContent = '—'; ram.classList.add('dim');
      }
    } catch { }
  }

  checkStatus();
  setTimeout(checkStatus, 3000);
  pollSystem();
  setInterval(pollSystem, 5000);
</script>
</body>
</html>
"""

# ── HTTP Handler ───────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass  # sessiz log

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._send(200, 'text/html; charset=utf-8', HTML.encode())
        elif self.path == '/api/status':
            self._json({'ok': _foundry_ready})
        elif self.path == '/api/system':
            self._json(get_system_stats())
        else:
            self._send(404, 'text/plain', b'Not found')

    def do_POST(self):
        if self.path == '/api/query':
            length = int(self.headers.get('Content-Length', 0))
            body   = json.loads(self.rfile.read(length))
            query  = body.get('query', '').strip()
            result = handle_query(query)
            self._json(result)
        else:
            self._send(404, 'text/plain', b'Not found')

    def _send(self, code, ct, data):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self._send(200, 'application/json', data)


# ── Foundry Local başlatma (uygulama açılırken bir kez) ───────
_foundry_ready = False

def init_foundry():
    global _foundry_ready
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
        config = Configuration(app_name="TrustRag")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance
        manager.catalog.get_model("qwen3-embedding-0.6b").load()
        manager.catalog.get_model("phi-3.5-mini").load()
        manager.start_web_service()
        _foundry_ready = True
        print("  Foundry Local hazır.")
    except Exception as e:
        print(f"  Foundry Local başlatılamadı: {e}")


# ── Sistem telemetrisi (gerçek veri; yoksa nazikçe düşer) ──────
def get_system_stats() -> dict:
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            'ok': True,
            'cpu_percent': psutil.cpu_percent(interval=0.12),
            'ram_percent': vm.percent,
            'ram_used_gb': round(vm.used / (1024 ** 3), 1),
            'ram_total_gb': round(vm.total / (1024 ** 3), 1),
        }
    except Exception:
        return {'ok': False}


# ── Query handler ──────────────────────────────────────────────
def handle_query(query: str) -> dict:
    t0 = time.perf_counter()
    if not _foundry_ready:
        return {'answer': '⏳ Foundry Local henüz yükleniyor, lütfen birkaç saniye bekleyin ve tekrar deneyin.', 'sources': [], 'latency': 0}
    try:
        from retrieval import get_top_chunks
        from generation import generate_answer
        chunks = get_top_chunks(query, top_k=3, threshold=0.25)
        answer = generate_answer(query)
        sources = [{'source': c['source'], 'similarity': round(c['similarity'], 3)} for c in chunks]
        return {'answer': answer, 'sources': sources, 'latency': round(time.perf_counter() - t0, 2)}
    except Exception as e:
        return {'answer': f'Hata: {e}', 'sources': [], 'latency': 0}


# ── Main ──────────────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=init_foundry, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f'\n  TrustRAG çalışıyor → http://localhost:{PORT}\n')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Kapatılıyor...')