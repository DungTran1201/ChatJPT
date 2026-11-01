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
            Đăng Nhập
          </Link>
          <Link
            href="/register"
            className="btn btn-primary"
            style={{ fontSize: '0.85rem', padding: '6px 16px' }}
          >
            Bắt Đầu Học Ngay
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
            <span>🌸 Nền Tảng Học Tiếng Nhật Thông Minh Cùng AI Sensei 3D</span>
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
            Làm Chủ Tiếng Nhật Cùng <span style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>ChatJPT</span>
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
            Hệ sinh thái học tiếng Nhật toàn diện tích hợp Trợ lý ảo AI 3D (Virtual Sensei), Luyện Kaiwa phản xạ thực chiến, Chấm chữa ngữ pháp (Grammar Doctor) và Tra cứu Hán tự chuyên sâu từ N5 đến N1.
          </p>

          <div style={{ display: 'flex', gap: '0.85rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link
              href="/chat"
              className="btn btn-primary"
              style={{ padding: '12px 28px', fontSize: '1rem', fontWeight: 600 }}
            >
              <span>Vào Không Gian Học Tập</span>
            </Link>

            <Link
              href="/rules"
              className="btn btn-secondary"
              style={{ padding: '12px 24px', fontSize: '1rem', fontWeight: 600 }}
            >
              <span>Kho Quy Tắc &amp; Prompts</span>
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
              desc: 'Gia sư ảo 3D biểu cảm tự nhiên, chớp mắt, nhịp thở và cử chỉ động viên sinh động theo từng câu trả lời.',
            },
            {
              icon: 'chat' as const,
              title: 'Luyện Kaiwa Phản Xạ',
              desc: 'Thực hành hội thoại theo tình huống thực tế (baito, mua sắm, phỏng vấn, công sở Keigo) phân loại JLPT N5 - N1.',
            },
            {
              icon: 'rules' as const,
              title: 'Grammar Doctor',
              desc: 'Tự động phát hiện lỗi sai trợ từ (は/が, に/で), thể động từ (Te, Ta, Nai, Bị động) và hướng dẫn sửa chi tiết.',
            },
            {
              icon: 'prompts' as const,
              title: 'Kanji & Furigana Breakdown',
              desc: 'Hiển thị Furigana, Romaji, Onyomi, Kunyomi và số nét Hán tự trực quan ngay trong khung đàm thoại.',
            },
            {
              icon: 'rules' as const,
              title: 'Rules & Prompts Sư Phạm',
              desc: 'Tùy biến linh hoạt bộ quy tắc giảng dạy và prompts mẫu với 4 chế độ kích hoạt thông minh (Always-on, Model decision, Glob, Manual).',
            },
            {
              icon: 'settings' as const,
              title: 'Bảo Vệ Khóa Cá Nhân (BYOK)',
              desc: 'Mã hóa AES-256 an toàn khóa API riêng (Gemini, OpenAI, Claude, DeepSeek, Groq) cùng cơ chế tự động Failover.',
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
        © 2026 ChatJPT — Hệ Sinh Thái Học Tiếng Nhật Thông Minh Tích Hợp AI Trợ Lý Ảo 3D.
      </footer>
    </div>
  );
}
