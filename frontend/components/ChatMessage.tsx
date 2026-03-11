type Props = {
  role: 'user' | 'assistant';
  text: string;
};

export default function ChatMessage({ role, text }: Props) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
          ? 'bg-emerald-600 text-white rounded-br-sm'
          : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm shadow-sm'
        }`}>
        {text}
      </div>
    </div>
  );
}
