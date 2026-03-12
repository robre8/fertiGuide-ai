'use client';
import ChatBox from '../components/ChatBox';
import dynamic from 'next/dynamic';

const SymptomClassifier = dynamic(
  () => import('../components/SymptomClassifier'),
  {
    ssr: false,
    loading: () => (
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <p className="text-sm text-gray-400">Loading symptom classifier...</p>
      </div>
    )
  }
);

const DocumentUpload = dynamic(
  () => import('../components/DocumentUpload'),
  { ssr: false }
);

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-emerald-800 mb-2">🧬 FertiGuide AI</h1>
          <p className="text-gray-500">Intelligent assistant for Assisted Reproductive Technology</p>
        </div>

        {/* Main layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-6">
            <DocumentUpload />
            <SymptomClassifier />
          </aside>

          <section className="lg:col-span-8">
            <ChatBox />
          </section>
        </div>
      </div>
    </main>
  );
}
