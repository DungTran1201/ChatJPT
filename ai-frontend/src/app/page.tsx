'use client';

import React from 'react';
import Link from 'next/link';
import Icon from '@/components/ui/Icon';

export default function HomePage() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
      {/* Navigation Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1rem 2rem',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface)',
          backdropFilter: 'blur(16px)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '1.05rem',
              boxShadow: '0 2px 8px rgba(236, 72, 153, 0.3)',
            }}
          >
            JP
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontSize: '1.2rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)'
              }}
            >
              ChatJPT
            </span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              Japanese Learning AI Sensei
            </span>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Link
            href="/chat"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 14px' }}
          >
            <Icon name="chat" size={14} />
            <span>Chat &amp; Kaiwa</span>
          </Link>
          <Link
            href="/rules"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 14px' }}
          >
            <Icon name="rules" size={14} />
            <span>Rules &amp; Prompts</span>
          </Link>
          <Link
            href="/login"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 14px' }}
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="btn btn-primary"
            style={{ fontSize: '0.85rem', padding: '6px 16px' }}
          >
            Get Started
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4rem 1.5rem',
          textAlign: 'center',
          position: 'relative',
        }}
      >
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '840px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 16px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(236, 72, 153, 0.12)',
              border: '1px solid rgba(236, 72, 153, 0.35)',
              color: '#f43f5e',
              fontSize: '0.85rem',
              fontWeight: 600,
              marginBottom: '1.5rem',
            }}
          >
            <span>🌸 Intelligent Japanese Learning Platform with 3D AI Sensei</span>
          </div>

          <h1
            style={{
              fontSize: 'clamp(2.4rem, 5.5vw, 3.8rem)',
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              marginBottom: '1.25rem',
              color: 'var(--text-primary)',
            }}
          >
            Master Japanese with <span style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>ChatJPT</span>
          </h1>

          <p
            style={{
              fontSize: '1.15rem',
              lineHeight: 1.65,
              color: 'var(--text-secondary)',
              marginBottom: '2rem',
              maxWidth: '680px',
              margin: '0 auto 2.25rem',
            }}
          >
            Comprehensive Japanese learning ecosystem featuring 3D Virtual Sensei, real-life conversational Kaiwa drills, pedagogical Grammar Doctor, and deep Kanji study from N5 to N1.
          </p>

          <div style={{ display: 'flex', gap: '0.85rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link
              href="/chat"
              className="btn btn-primary"
              style={{ padding: '12px 28px', fontSize: '1rem', fontWeight: 600 }}
            >
              <span>Enter Learning Workspace</span>
            </Link>

            <Link
              href="/rules"
              className="btn btn-secondary"
              style={{ padding: '12px 24px', fontSize: '1rem', fontWeight: 600 }}
            >
              <span>Rules &amp; Prompts Library</span>
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <section
          style={{
            marginTop: '4.5rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '1.25rem',
            maxWidth: '1060px',
            width: '100%',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {[
            {
              icon: 'chat' as const,
              title: '3D VRM Virtual Sensei',
              desc: 'Interactive 3D tutor with natural facial expressions, blinking, breathing cycles, and encouraging gestures.',
            },
            {
              icon: 'chat' as const,
              title: 'Reflexive Kaiwa Practice',
              desc: 'Practice real-life conversational dialogue (part-time work, shopping, interviews, Keigo business contexts) across JLPT N5 - N1.',
            },
            {
              icon: 'rules' as const,
              title: 'Grammar Doctor',
              desc: 'Automated detection of particle mistakes (wa/ga, ni/de), verb conjugations, and thorough pedagogical feedback.',
            },
            {
              icon: 'prompts' as const,
              title: 'Kanji & Furigana Breakdown',
              desc: 'Dynamic Furigana ruby, Hepburn romaji, stroke order, and detailed readings displayed right inside the chat.',
            },
            {
              icon: 'rules' as const,
              title: 'Pedagogical Rules & Prompts',
              desc: 'Customizable pedagogical rule sets and companion system prompts with 4 smart trigger modes (Always-on, Model decision, Glob, Manual).',
            },
            {
              icon: 'settings' as const,
              title: 'Bring Your Own Key (BYOK)',
              desc: 'AES-256 secure encryption for personal API keys (Gemini, OpenAI, Claude, Groq) with seamless auto-failover.',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="card"
              style={{
                padding: '1.35rem',
                textAlign: 'left',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface)',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              <div style={{ color: 'var(--accent)', marginBottom: '0.85rem' }}>
                <Icon name={item.icon} size={22} />
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: 650, marginBottom: '0.45rem', color: 'var(--text-primary)' }}>{item.title}</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>{item.desc}</p>
            </div>
          ))}
        </section>
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '1.5rem',
          textAlign: 'center',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          background: 'var(--bg-surface)',
        }}
      >
        © 2026 ChatJPT — Intelligent Japanese Learning Platform with 3D AI Assistant.
      </footer>
    </div>
  );
}
