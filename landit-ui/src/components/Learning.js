import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, MessageSquare, RefreshCw, Sparkles } from 'lucide-react';
import LearningPlan from './LearningPlan';

const Learning = ({ userEmail, jobContext, onClearJobContext }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activePlan, setActivePlan] = useState(null);
  const [activeJobContext, setActiveJobContext] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (messages.length === 0) {
      setIsTyping(true);
      setTimeout(() => {
        setMessages([{
          id: 1,
          type: 'bot',
          content: `Hi! I'm your AI Learning Coach. I can help you create personalized learning plans, suggest projects, and answer questions about skill development. What would you like to work on today?`,
          timestamp: new Date()
        }]);
        setIsTyping(false);
      }, 1500); // Simulate typing delay
    }
  }, [messages.length]);

  useEffect(() => {
      if (jobContext) {
        console.log('Job Context received:', jobContext);
        console.log('Job ID:', jobContext.job_id);
        console.log('Recommendation ID:', jobContext.recommendation_id);

        const jobMessage = `Create a learning plan for the ${jobContext.title} position at ${jobContext.company}. I'm interested in this role and want to bridge the skill gaps.`;
        const userMessage = { id: Date.now(), type: 'user', content: jobMessage, timestamp: new Date() };

        setMessages(prev => [...prev, userMessage]);
        setActiveJobContext(jobContext);
        handleGeneratePlan(jobContext);

        if (onClearJobContext) {
          onClearJobContext();
        }
      }
    }, [jobContext, onClearJobContext]);

  const simulateTyping = (responseText, callback) => {
    setIsTyping(true);

    // Calculate typing speed (adjust for longer/shorter messages)
    const baseDelay = 30; // ms per character
    const minDelay = 1000; // minimum typing time
    const maxDelay = 3000; // maximum typing time
    const calculatedDelay = Math.min(maxDelay, Math.max(minDelay, responseText.length * baseDelay));

    setTimeout(() => {
      callback();
      setIsTyping(false);
    }, calculatedDelay);
  };

  const handleGeneratePlan = async (jobData) => {
      setIsLoading(true);

      if (!jobData || !jobData.job_id) {
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: `I'm sorry, but I'm missing required information (job ID) to generate this plan. Please try selecting the job again.`,
          timestamp: new Date(),
          isError: true
        };

        simulateTyping(errorMessage.content, () => {
          setMessages(prev => [...prev, errorMessage]);
        });

        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/generate-learning-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_email: userEmail,
            job_id: jobData.job_id,
            recommendation_id: jobData.recommendation_id
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate the learning plan.');
        }

        const data = await response.json();
        setActivePlan(data.learning_plan);

      } catch (error) {
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: `I encountered an error generating your learning plan: ${error.message || 'Unknown error'}. Please try again or select another job.`,
          timestamp: new Date(),
          isError: true
        };

        simulateTyping(errorMessage.content, () => {
          setMessages(prev => [...prev, errorMessage]);
        });
      } finally {
        setIsLoading(false);
      }
    };

  const sendMessage = () => {
    if (!inputMessage.trim() || isLoading || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Simulate AI thinking and responding
    setIsTyping(true);

    setTimeout(() => {
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "To generate a personalized learning plan, please select a job from the 'Jobs' tab and click 'Get Learning Plan'. I can then create a customized roadmap to help you bridge any skill gaps for that specific role.",
        timestamp: new Date()
      };

      simulateTyping(botMessage.content, () => {
        setMessages(prev => [...prev, botMessage]);
      });
    }, 800); // Small delay before starting to "type"
  };

  const handleQuickAction = (action) => {
    if (isLoading || isTyping) return;

    setInputMessage(action);
    // Auto-send after a brief moment
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (activePlan && activeJobContext) {
    return (
      <LearningPlan
        userEmail={userEmail}
        jobMatch={activeJobContext}
        existingPlan={activePlan}
        onBack={() => {
          setActivePlan(null);
          setActiveJobContext(null);
        }}
      />
    );
  }

  // Typing Indicator Component
  const TypingIndicator = () => (
    <div className="flex gap-4 justify-start" style={{ animation: 'fadeInUp 0.3s ease-out' }}>
      <div style={{
        width: '40px',
        height: '40px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
      }}>
        <Bot className="w-5 h-5 text-white" />
      </div>
      <div style={{
        background: 'rgba(255,255,255,0.8)',
        padding: '16px 20px',
        borderRadius: '18px 18px 18px 6px',
        border: '1px solid rgba(0,0,0,0.05)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
      }}>
        <div className="flex items-center gap-3 text-gray-600">
          <div className="flex gap-1">
            <div style={{
              width: '8px',
              height: '8px',
              backgroundColor: '#667eea',
              borderRadius: '50%',
              animation: 'typingBounce 1.4s infinite ease-in-out both'
            }}></div>
            <div style={{
              width: '8px',
              height: '8px',
              backgroundColor: '#667eea',
              borderRadius: '50%',
              animation: 'typingBounce 1.4s infinite ease-in-out both',
              animationDelay: '0.16s'
            }}></div>
            <div style={{
              width: '8px',
              height: '8px',
              backgroundColor: '#667eea',
              borderRadius: '50%',
              animation: 'typingBounce 1.4s infinite ease-in-out both',
              animationDelay: '0.32s'
            }}></div>
          </div>
          <span className="text-sm" style={{ color: '#667eea', fontWeight: '500' }}>AI is thinking...</span>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(20px)',
      borderRadius: '24px',
      border: '1px solid rgba(255,255,255,0.3)',
      boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
      height: '80vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Modern Header with Gradient */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '24px',
        color: 'white'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backdropFilter: 'blur(10px)'
          }}>
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '28px', fontWeight: '700' }}>AI Learning Coach</h1>
            <p style={{ margin: 0, opacity: 0.9, fontSize: '14px' }}>
              Get personalized learning plans and career guidance
            </p>
          </div>
        </div>
      </div>

      {/* Quick Action Buttons */}
      {messages.length <= 2 && !isTyping && (
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(0,0,0,0.05)'
        }}>
          <p style={{
            fontSize: '14px',
            color: '#6b7280',
            marginBottom: '12px',
            textAlign: 'center'
          }}>
            Quick actions:
          </p>
          <div style={{
            display: 'flex',
            gap: '8px',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            {[
              'Create learning plan',
              'Skill gap analysis',
              'Career path advice',
              'Project suggestions'
            ].map((action, index) => (
              <button
                key={index}
                onClick={() => handleQuickAction(action)}
                disabled={isTyping}
                style={{
                  padding: '8px 16px',
                  background: 'rgba(102, 126, 234, 0.1)',
                  color: '#667eea',
                  border: '1px solid rgba(102, 126, 234, 0.2)',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: '500',
                  cursor: isTyping ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  opacity: isTyping ? 0.6 : 1
                }}
                onMouseOver={(e) => {
                  if (!isTyping) {
                    e.target.style.background = 'rgba(102, 126, 234, 0.2)';
                    e.target.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseOut={(e) => {
                  if (!isTyping) {
                    e.target.style.background = 'rgba(102, 126, 234, 0.1)';
                    e.target.style.transform = 'translateY(0)';
                  }
                }}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            style={{ animation: 'fadeInUp 0.3s ease-out' }}
          >
            {message.type === 'bot' && (
              <div style={{
                width: '40px',
                height: '40px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}

            <div style={{
              maxWidth: '70%',
              background: message.type === 'user'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : message.isError
                  ? '#fef2f2'
                  : 'rgba(255,255,255,0.8)',
              color: message.type === 'user' ? 'white' : message.isError ? '#dc2626' : '#1f2937',
              padding: '16px 20px',
              borderRadius: message.type === 'user' ? '18px 18px 6px 18px' : '18px 18px 18px 6px',
              border: message.type === 'bot' && !message.isError ? '1px solid rgba(0,0,0,0.05)' :
                     message.isError ? '1px solid #fecaca' : 'none',
              boxShadow: message.type === 'bot' && !message.isError ? '0 4px 12px rgba(0,0,0,0.05)' :
                        message.type === 'user' ? '0 4px 12px rgba(102, 126, 234, 0.2)' :
                        message.isError ? '0 4px 12px rgba(220, 38, 38, 0.1)' : 'none',
              lineHeight: '1.5'
            }}>
              <div className="whitespace-pre-wrap text-sm">
                {message.content}
              </div>
              <div style={{
                fontSize: '11px',
                opacity: 0.7,
                marginTop: '8px',
                textAlign: message.type === 'user' ? 'right' : 'left'
              }}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>

            {message.type === 'user' && (
              <div style={{
                width: '40px',
                height: '40px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <User className="w-5 h-5 text-white" />
              </div>
            )}
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && <TypingIndicator />}

        {/* Enhanced Loading State for Plan Generation */}
        {isLoading && (
          <div className="flex gap-4 justify-start">
            <div style={{
              width: '40px',
              height: '40px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div style={{
              background: 'rgba(255,255,255,0.8)',
              padding: '16px 20px',
              borderRadius: '18px 18px 18px 6px',
              border: '1px solid rgba(0,0,0,0.05)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
            }}>
              <div className="flex items-center gap-3 text-gray-600">
                <div className="flex gap-1">
                  <div style={{
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#667eea',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s infinite ease-in-out both'
                  }}></div>
                  <div style={{
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#667eea',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s infinite ease-in-out both',
                    animationDelay: '0.16s'
                  }}></div>
                  <div style={{
                    width: '6px',
                    height: '6px',
                    backgroundColor: '#667eea',
                    borderRadius: '50%',
                    animation: 'bounce 1.4s infinite ease-in-out both',
                    animationDelay: '0.32s'
                  }}></div>
                </div>
                <span className="text-sm">Generating your learning plan...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Modern Input Area */}
      <div style={{
        padding: '20px',
        background: 'rgba(248, 250, 252, 0.8)',
        borderTop: '1px solid rgba(0,0,0,0.05)'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          background: 'white',
          borderRadius: '16px',
          padding: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
          border: '1px solid rgba(0,0,0,0.05)'
        }}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about skill development, learning paths, or career guidance..."
            style={{
              flex: 1,
              border: 'none',
              padding: '12px 16px',
              borderRadius: '12px',
              resize: 'none',
              fontSize: '14px',
              fontFamily: 'inherit',
              outline: 'none',
              background: 'transparent',
              minHeight: '44px',
              maxHeight: '120px'
            }}
            rows="1"
            disabled={isLoading || isTyping}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading || isTyping}
            style={{
              width: '44px',
              height: '44px',
              background: inputMessage.trim() && !isLoading && !isTyping
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#e5e7eb',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: inputMessage.trim() && !isLoading && !isTyping ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
              opacity: inputMessage.trim() && !isLoading && !isTyping ? 1 : 0.6
            }}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Add CSS for animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }
        
        @keyframes typingBounce {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default Learning;