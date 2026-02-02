import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { GlowingEffect } from './ui/glowing-effect';

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm Aishwarya's AI assistant. Ask me anything about her skills, experience, projects, or GitHub repositories!",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'assistant',
        content: "Sorry, I'm having trouble connecting right now. Please make sure the backend server is running on port 8000.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 group"
          aria-label="Open chat"
        >
          <div className="relative">
            {/* Button */}
            <div className="relative bg-white/10 backdrop-blur-sm p-4 rounded-full border border-gray-300/20 hover:bg-white/20 transition-all duration-300 hover:scale-110 shadow-xl">
              <MessageCircle className="w-6 h-6 text-gray-300" />
            </div>
            
            {/* Pulse indicator */}
            <span className="absolute top-0 right-0 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gray-300 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-gray-300"></span>
            </span>
          </div>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[380px] h-[600px] flex flex-col">
          <div className="relative rounded-lg border-[0.75px] border-gray-300/20 p-[2px] h-full">
            <GlowingEffect
              spread={30}
              glow={true}
              disabled={false}
              proximity={64}
              inactiveZone={0.01}
              borderWidth={2}
            />
            <Card className="relative z-10 flex flex-col h-full bg-black/95 backdrop-blur-xl border-gray-300/10 shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-300/10">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="relative bg-white/10 p-2 rounded-full border border-gray-300/20">
                      <Bot className="w-5 h-5 text-gray-300" />
                    </div>
                    <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-black rounded-full"></span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#f5f5f7]">AI Assistant</h3>
                    <p className="text-xs text-gray-400 font-normal">Ask me anything</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-[#f5f5f7] hover:bg-white/5"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex gap-3 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role === 'assistant' && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/10 border border-gray-300/20 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-gray-300" />
                        </div>
                      )}
                      
                      <div
                        className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                          message.role === 'user'
                            ? 'bg-white/10 text-[#f5f5f7] border border-gray-300/20'
                            : 'bg-black border border-gray-300/20 text-gray-300'
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap font-normal">
                          {message.content}
                        </p>
                        <span className="text-[10px] opacity-50 mt-1 block">
                          {message.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </span>
                      </div>

                      {message.role === 'user' && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/10 border border-gray-300/20 flex items-center justify-center">
                          <User className="w-4 h-4 text-gray-300" />
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/10 border border-gray-300/20 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-gray-300" />
                      </div>
                      <div className="bg-black border border-gray-300/20 rounded-2xl px-4 py-3 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                        <span className="text-sm text-gray-400 font-normal">Thinking...</span>
                      </div>
                    </div>
                  )}
                  
                  <div ref={scrollRef} />
                </div>
              </ScrollArea>

              {/* Input */}
              <div className="p-4 border-t border-gray-300/10">
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about skills, projects..."
                    disabled={isLoading}
                    className="flex-1 bg-black border-gray-300/20 text-gray-300 font-normal placeholder:text-gray-400 focus:border-gray-300/40"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={isLoading || !input.trim()}
                    className="bg-white/10 hover:bg-white/20 text-gray-300 border border-gray-300/20"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-[10px] text-gray-500 mt-2 text-center font-normal">
                  Powered by RAG + Ollama (llama3)
                </p>
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
