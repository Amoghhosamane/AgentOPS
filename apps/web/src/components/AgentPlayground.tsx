'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Square,
  Bot,
  User,
  ExternalLink,
  RotateCcw,
  Sparkles,
  Clock,
  Zap,
  Wrench,
  CheckCircle2
} from 'lucide-react';
import { API_BASE, DEFAULT_PROJECT_ID } from '../lib/api';

interface StepEvent {
  step: number;
  name: string;
  description?: string;
  tool_name?: string;
  args?: any;
  result?: any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  traceId?: string;
  steps?: StepEvent[];
  durationMs?: number;
}

export function AgentPlayground({ onOpenTrace }: { onOpenTrace: (traceId: string) => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome to the **AgentOps Interactive Playground**.\n\nAsk a research question or request numerical data analysis. Every step, tool invocation, and token consumption is recorded in real-time OpenTelemetry traces.',
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('research');
  const [isRunning, setIsRunning] = useState(false);
  const [activeSteps, setActiveSteps] = useState<StepEvent[]>([]);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeSteps]);

  const handleSend = async () => {
    if (!input.trim() || isRunning) return;

    const userText = input.trim();
    setInput('');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: userText };
    setMessages((prev) => [...prev, userMsg]);
    setIsRunning(true);
    setActiveSteps([]);

    const abortController = new AbortController();
    eventSourceRef.current = abortController;

    const assistantMsgId = (Date.now() + 1).toString();
    let accumulatedContent = '';
    let currentTraceId = '';
    const stepsAccumulator: StepEvent[] = [];

    try {
      const response = await fetch(`${API_BASE}/api/v1/agent-runs?project_id=${DEFAULT_PROJECT_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userText,
          stream: true,
          provider: 'mock',
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`Failed to execute agent run: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No readable stream');

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          const [eventLine, ...dataLines] = block.split('\n');
          const eventType = eventLine.replace('event: ', '').trim();
          const dataStr = dataLines.join('\n').replace('data: ', '').trim();
          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);

            if (eventType === 'agent_started') {
              setCurrentRunId(data.run_id);
              currentTraceId = data.trace_id;
            } else if (eventType === 'step_started') {
              const step: StepEvent = { step: data.step, name: data.name, description: data.description };
              stepsAccumulator.push(step);
              setActiveSteps([...stepsAccumulator]);
            } else if (eventType === 'tool_executing') {
              const step: StepEvent = {
                step: data.step,
                name: 'tool_call',
                tool_name: data.tool_name,
                args: data.args,
              };
              stepsAccumulator.push(step);
              setActiveSteps([...stepsAccumulator]);
            } else if (eventType === 'tool_result') {
              const existing = stepsAccumulator.find((s) => s.step === data.step && s.tool_name === data.tool_name);
              if (existing) {
                existing.result = data.result;
              } else {
                stepsAccumulator.push({ step: data.step, name: 'tool_result', tool_name: data.tool_name, result: data.result });
              }
              setActiveSteps([...stepsAccumulator]);
            } else if (eventType === 'token') {
              accumulatedContent += data.chunk;
              setMessages((prev) => {
                const filtered = prev.filter((m) => m.id !== assistantMsgId);
                return [
                  ...filtered,
                  {
                    id: assistantMsgId,
                    role: 'assistant',
                    content: accumulatedContent,
                    traceId: currentTraceId,
                    steps: [...stepsAccumulator],
                  },
                ];
              });
            } else if (eventType === 'agent_completed') {
              setMessages((prev) => {
                const filtered = prev.filter((m) => m.id !== assistantMsgId);
                return [
                  ...filtered,
                  {
                    id: assistantMsgId,
                    role: 'assistant',
                    content: accumulatedContent,
                    traceId: currentTraceId,
                    steps: [...stepsAccumulator],
                    durationMs: data.duration_ms,
                  },
                ];
              });
            }
          } catch (e) {
            console.error('Error parsing SSE frame:', e);
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 2).toString(),
            role: 'assistant',
            content: `**Error:** ${err.message || 'Workflow failed'}`,
          },
        ]);
      }
    } finally {
      setIsRunning(false);
      setActiveSteps([]);
      setCurrentRunId(null);
      eventSourceRef.current = null;
    }
  };

  const handleStop = async () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
    }
    if (currentRunId) {
      try {
        await fetch(`${API_BASE}/api/v1/agent-runs/${currentRunId}/cancel`, { method: 'POST' });
      } catch (e) {
        console.error('Failed to cancel run:', e);
      }
    }
    setIsRunning(false);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#090E1A]">
      {/* Top Bar / Model Selector */}
      <header className="h-14 border-b border-gray-800 bg-[#111827]/80 backdrop-blur px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-semibold text-white">Agent Playground</span>
          <span className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
            Live Execution Mode
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-xs rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:border-blue-500"
          >
            <option value="research">Research Assistant (ReAct Loop)</option>
            <option value="analysis">Data Analysis Assistant (Deterministic Tools)</option>
          </select>
          <div className="flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Local Offline Ready</span>
          </div>
        </div>
      </header>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-16 lg:px-32 space-y-6">
        {messages.map((m) => (
          <div key={m.id} className="flex space-x-4 max-w-4xl mx-auto">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-blue-400 border border-gray-700'
              }`}
            >
              {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className="flex-1 space-y-3 overflow-hidden">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-gray-300">
                  {m.role === 'user' ? 'You' : 'AgentOps Assistant'}
                </span>
                {m.durationMs && (
                  <span className="text-[11px] text-gray-500 font-mono">({m.durationMs}ms)</span>
                )}
              </div>

              {/* Steps Accordion / Badge */}
              {m.steps && m.steps.length > 0 && (
                <div className="p-3 bg-gray-900/90 border border-gray-800 rounded-lg text-xs space-y-2">
                  <div className="font-semibold text-gray-400 uppercase tracking-wider text-[10px] flex items-center space-x-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    <span>Observable Execution Steps ({m.steps.length})</span>
                  </div>
                  {m.steps.map((st, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-gray-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-mono text-blue-400 font-medium">[{st.name}]</span>{' '}
                        {st.tool_name && <span className="text-amber-300">tool: {st.tool_name}</span>}{' '}
                        {st.description && <span>— {st.description}</span>}
                        {st.result && (
                          <div className="mt-1 p-1.5 bg-black/40 rounded font-mono text-[11px] text-gray-400 overflow-x-auto">
                            Result: {typeof st.result === 'object' ? JSON.stringify(st.result) : st.result}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Message Content */}
              <div className="prose prose-invert text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                {m.content}
              </div>

              {/* View Trace Button */}
              {m.traceId && (
                <button
                  onClick={() => onOpenTrace(m.traceId!)}
                  className="inline-flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 bg-blue-950/40 border border-blue-800/60 px-2.5 py-1 rounded-md transition"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>View Trace Waterfall</span>
                </button>
              )}
            </div>
          </div>
        ))}

        {/* In-Flight Active Steps Indicator */}
        {isRunning && (
          <div className="flex space-x-4 max-w-4xl mx-auto">
            <div className="w-8 h-8 rounded-full bg-gray-800 text-blue-400 border border-gray-700 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4 animate-spin text-blue-400" />
            </div>
            <div className="flex-1 p-4 bg-gray-900 border border-blue-900/50 rounded-lg text-xs space-y-2 animate-pulse">
              <div className="font-semibold text-blue-400 flex items-center space-x-2">
                <span>Agent Workflow Executing...</span>
              </div>
              {activeSteps.map((s, idx) => (
                <div key={idx} className="flex items-center space-x-2 text-gray-300">
                  <Wrench className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                  <span className="font-mono text-blue-300">Step {s.step}: {s.name}</span>
                  {s.tool_name && <span className="text-amber-300">({s.tool_name})</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Bottom Area */}
      <div className="p-4 border-t border-gray-800 bg-[#111827]">
        <div className="max-w-4xl mx-auto relative flex items-center">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask research query or analyze dataset metrics... (Press Enter to send)"
            rows={2}
            className="w-full bg-[#1F2937] border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none pr-24"
          />

          <div className="absolute right-3 flex items-center space-x-2">
            {isRunning ? (
              <button
                onClick={handleStop}
                className="p-2 rounded-lg bg-red-600 hover:bg-red-500 text-white transition flex items-center space-x-1"
                title="Stop Execution"
              >
                <Square className="w-4 h-4" />
                <span className="text-xs font-semibold pr-1">Stop</span>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="p-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white transition"
                title="Send Message"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
