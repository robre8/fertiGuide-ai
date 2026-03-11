'use client';
import { ApolloProvider } from '@apollo/client';
import { apolloClient } from '../lib/apollo';
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

export default function Home() {
  return (
    <ApolloProvider client={apolloClient}>
      <main className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-emerald-800 mb-2">🧬 FertiGuide AI</h1>
            <p className="text-gray-500">Intelligent assistant for Assisted Reproductive Technology</p>
          </div>

          {/* Main layout */}
          <div className="grid grid-cols-1 gap-8">
            <ChatBox />
            <SymptomClassifier />
          </div>
        </div>
      </main>
    </ApolloProvider>
  );
}
