'use client';
import { useState, useEffect, useRef } from 'react';

const CATEGORIES = [
  'hormonal imbalance',
  'anatomical or structural issue',
  'genetic or chromosomal factor',
  'male factor infertility',
  'lifestyle or environmental factor',
  'endometriosis',
  'ovarian reserve issue',
];

type Result = {
  label: string;
  score: number;
};

type ZeroShotOutput = {
  labels: string[];
  scores: number[];
};

type ZeroShotClassifier = (
  text: string,
  labels: string[],
  options: { multi_label: boolean }
) => Promise<ZeroShotOutput | ZeroShotOutput[]>;

export default function SymptomClassifier() {
  const [symptom, setSymptom] = useState('');
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');

  const classifierRef = useRef<ZeroShotClassifier | null>(null);

  useEffect(() => {
    const loadModel = async () => {
      try {
        setModelStatus('loading');
        const { pipeline } = await import('@xenova/transformers');
        classifierRef.current = (await pipeline(
          'zero-shot-classification',
          'Xenova/nli-deberta-v3-small'
        )) as unknown as ZeroShotClassifier;
        setModelStatus('ready');
      } catch (err) {
        console.error('Model load error:', err);
        setModelStatus('error');
      }
    };
    loadModel();
  }, []);

  const classify = async () => {
    if (!symptom.trim() || !classifierRef.current || loading) return;

    setLoading(true);
    setResults([]);

    try {
      const rawOutput = await classifierRef.current(symptom, CATEGORIES, {
        multi_label: true,
      });
      const output = (Array.isArray(rawOutput) ? rawOutput[0] : rawOutput) as ZeroShotOutput | undefined;
      if (!output) {
        return;
      }

      const sorted = output.labels
        .map((label: string, i: number) => ({ label, score: output.scores[i] }))
        .sort((a: Result, b: Result) => b.score - a.score)
        .slice(0, 3);

      setResults(sorted);
    } catch (err) {
      console.error('Classification error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch (modelStatus) {
      case 'idle':
        return null;
      case 'loading':
        return (
          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full">⏳ Loading ONNX model...</span>
        );
      case 'ready':
        return (
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">✅ Model ready</span>
        );
      case 'error':
        return (
          <span className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">❌ Model failed to load</span>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score > 0.7) return 'bg-emerald-500';
    if (score > 0.4) return 'bg-amber-400';
    return 'bg-gray-300';
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Symptom Classifier</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Powered by <span className="font-medium text-emerald-600">DeBERTa ONNX</span> — runs entirely in your browser
          </p>
        </div>
        {getStatusBadge()}
      </div>

      <textarea
        value={symptom}
        onChange={(e) => setSymptom(e.target.value)}
        placeholder="Describe your symptoms... e.g. 'I have irregular periods, elevated FSH levels and pain during menstruation'"
        rows={3}
        className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder:text-gray-500 mb-3 focus:outline-none focus:border-emerald-500 resize-none"
      />

      <button
        onClick={classify}
        disabled={loading || modelStatus !== 'ready' || !symptom.trim()}
        className="w-full bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors mb-4"
      >
        {loading ? 'Classifying...' : 'Classify Symptoms'}
      </button>

      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-gray-700 font-medium uppercase tracking-wide">Top categories</p>
          {results.map((r, i) => (
            <div key={i}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-900 capitalize">{r.label}</span>
                <span className="text-xs font-semibold text-gray-700">{Math.round(r.score * 100)}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className={`h-2 rounded-full transition-all ${getScoreColor(r.score)}`} style={{ width: `${Math.round(r.score * 100)}%` }} />
              </div>
            </div>
          ))}
          <p className="text-xs text-gray-600 mt-2">⚠️ For informational purposes only. Always consult a specialist.</p>
        </div>
      )}
    </div>
  );
}
