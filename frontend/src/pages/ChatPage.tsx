import { useState, useRef, useEffect } from 'react'
import { Send, Brain, Plus, Loader2, Map } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import type { ChatMessage, ChatSession } from '@/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, any>
}

const STARTERS = [
  "I want to become an AI Engineer in 12 months",
  "What should I learn next for Data Science?",
  "Help me crack GATE CSE exam",
  "Build a roadmap for Full Stack Development",
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "👋 Hi! I'm **NeuraLearn AI**, your personal learning mentor.\n\nTell me about yourself and your goal — I'll analyze your skills, identify gaps, and create a personalized roadmap just for you!\n\n**Try saying:** *\"I'm a 2nd year CS student. I know Python and basic ML. I want to become an AI Engineer in 12 months.\"*",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [roadmapGenerated, setRoadmapGenerated] = useState(false)
  const [generatedRoadmapId, setGeneratedRoadmapId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text?: string) => {
    const content = text || input.trim()
    if (!content || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content }])
    setLoading(true)

    try {
      const { data } = await api.post('/chat/message', {
        content,
        session_id: sessionId || undefined,
      })

      setSessionId(data.session_id)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message.content,
        metadata: data.message.metadata,
      }])

      if (data.roadmap_generated) {
        setRoadmapGenerated(true)
        setGeneratedRoadmapId(data.roadmap_id)
        toast.success('🎉 Roadmap generated!', { duration: 5000 })
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to send message')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again.",
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-white text-sm">AI Mentor</h1>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs text-gray-400">Online</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => { setMessages([{ role: 'assistant', content: "👋 Starting a new conversation! Tell me your learning goal." }]); setSessionId(null) }}
          className="btn-secondary flex items-center gap-2 text-sm py-2"
        >
          <Plus className="w-4 h-4" /> New Chat
        </button>
      </div>

      {/* Roadmap notification */}
      {roadmapGenerated && generatedRoadmapId && (
        <div className="mb-3 glass-card p-3 border-primary-500/40 flex items-center justify-between">
          <span className="text-sm text-primary-300">🗺️ Your personalized roadmap is ready!</span>
          <Link to="/dashboard/roadmap" className="btn-primary text-xs py-1.5">
            View Roadmap <Map className="w-3 h-3 ml-1 inline" />
          </Link>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 pr-1 pb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-2`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex-shrink-0 flex items-center justify-center mb-1">
                <Brain className="w-3.5 h-3.5 text-white" />
              </div>
            )}
            <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
              <ReactMarkdown
                className="prose prose-invert prose-sm max-w-none prose-p:mb-1 prose-ul:mb-1 prose-li:mb-0 prose-headings:text-primary-300"
              >
                {msg.content}
              </ReactMarkdown>
              {msg.metadata?.roadmap_generated && (
                <div className="mt-2 pt-2 border-t border-white/10">
                  <span className="text-xs text-primary-300">✨ Roadmap generated</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-end gap-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex-shrink-0 flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="chat-bubble-ai flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-400" />
              <span className="text-sm text-gray-400">NeuraLearn is thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starter prompts */}
      {messages.length === 1 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {STARTERS.map(s => (
            <button key={s} onClick={() => sendMessage(s)}
              className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-gray-300 hover:border-primary-500/40 hover:text-white transition-all">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="glass-card p-2 flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tell me your goal, ask about skills, or request a study plan..."
          rows={1}
          className="flex-1 bg-transparent px-3 py-2 text-gray-100 placeholder-gray-500 outline-none resize-none text-sm max-h-32 overflow-y-auto scrollbar-thin"
          style={{ minHeight: '40px' }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 flex items-center justify-center flex-shrink-0 disabled:opacity-40 hover:from-primary-500 hover:to-primary-400 transition-all"
        >
          {loading ? <Loader2 className="w-4 h-4 text-white animate-spin" /> : <Send className="w-4 h-4 text-white" />}
        </button>
      </div>
    </div>
  )
}
