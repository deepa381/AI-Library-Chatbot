import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatApi } from '../api/chat';
import { useChatStore } from '../store/chatStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'react-hot-toast';
import { MessageSquare, Plus, Send, Trash2, Copy, Bot, User } from 'lucide-react';
import { cn } from '../lib/utils';

const SUGGESTED_PROMPTS = [
  "Recommend me a beginner Python book",
  "Find books about machine learning",
  "What books are available right now?",
  "Recommend some inspirational biographies"
];

export function ChatPage() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { activeSessionId, setActiveSession } = useChatStore();

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: chatApi.getSessions,
  });

  const { data: currentSession, isLoading: loadingMessages } = useQuery({
    queryKey: ['chatSession', activeSessionId],
    queryFn: () => chatApi.getSession(activeSessionId!),
    enabled: !!activeSessionId,
  });

  const sendMutation = useMutation({
    mutationFn: (message: string) => chatApi.sendMessage(message, activeSessionId || undefined),
    onSuccess: (data) => {
      if (!activeSessionId && data.session_id) {
        setActiveSession(data.session_id);
      }
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      queryClient.invalidateQueries({ queryKey: ['chatSession', data.session_id || activeSessionId] });
      setInput('');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to send message');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chatApi.deleteSession(id),
    onSuccess: (_, id) => {
      toast.success('Session deleted');
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      if (activeSessionId === id) {
        setActiveSession(null);
      }
    }
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, sendMutation.isPending]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sendMutation.isPending) return;
    sendMutation.mutate(input);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-xl border bg-card shadow-sm">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/20 flex flex-col hidden md:flex">
        <div className="p-4 border-b">
          <Button 
            className="w-full justify-start" 
            variant="outline"
            onClick={() => setActiveSession(null)}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {loadingSessions ? (
            Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)
          ) : sessions?.map((session: any) => (
            <div
              key={session.session_id}
              className={cn(
                "group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm",
                activeSessionId === session.session_id 
                  ? "bg-primary/10 text-primary font-medium" 
                  : "hover:bg-muted text-muted-foreground"
              )}
              onClick={() => setActiveSession(session.session_id)}
            >
              <div className="flex items-center truncate">
                <MessageSquare className="mr-2 h-4 w-4 shrink-0" />
                <span className="truncate">{session.title || 'New Conversation'}</span>
              </div>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMutation.mutate(session.session_id);
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-destructive p-1 rounded-md"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {!activeSessionId && (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-2xl mx-auto">
              <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Librarian AI</h2>
              <p className="text-muted-foreground mb-8">
                Ask me about our catalog, request recommendations, or check availability.
              </p>
              
              <div className="grid sm:grid-cols-2 gap-3 w-full">
                {SUGGESTED_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => sendMutation.mutate(prompt)}
                    className="p-4 text-sm text-left rounded-xl border bg-card hover:bg-muted/50 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeSessionId && loadingMessages && (
            <div className="space-y-4">
              <Skeleton className="h-20 w-3/4 rounded-2xl rounded-tl-sm" />
              <Skeleton className="h-20 w-3/4 ml-auto rounded-2xl rounded-tr-sm" />
            </div>
          )}

          {currentSession?.messages?.map((msg: any) => (
            <div key={msg.id} className={cn(
              "flex gap-4 max-w-[85%]",
              msg.sender === 'user' ? "ml-auto flex-row-reverse" : ""
            )}>
              <div className={cn(
                "h-8 w-8 shrink-0 rounded-full flex items-center justify-center",
                msg.sender === 'user' ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
              )}>
                {msg.sender === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>
              
              <div className="group relative flex flex-col gap-2">
                <div className={cn(
                  "p-4 rounded-2xl text-sm",
                  msg.sender === 'user' 
                    ? "bg-primary text-primary-foreground rounded-tr-sm" 
                    : "bg-muted rounded-tl-sm"
                )}>
                  {msg.sender === 'user' ? (
                    msg.content
                  ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
                
                {msg.sender === 'assistant' && (
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => handleCopy(msg.content)}
                      className="text-muted-foreground hover:text-foreground flex items-center text-xs gap-1"
                    >
                      <Copy className="h-3 w-3" /> Copy
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {sendMutation.isPending && (
            <div className="flex gap-4 max-w-[85%]">
              <div className="h-8 w-8 shrink-0 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="bg-muted p-4 rounded-2xl rounded-tl-sm flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-foreground/40 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1.5 h-1.5 bg-foreground/40 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-1.5 bg-foreground/40 rounded-full animate-bounce"></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-background">
          <form onSubmit={handleSubmit} className="flex gap-2 max-w-4xl mx-auto">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
              disabled={sendMutation.isPending}
            />
            <Button type="submit" disabled={!input.trim() || sendMutation.isPending}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] text-muted-foreground">
              Librarian AI can make mistakes. Verify availability before visiting the library.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
