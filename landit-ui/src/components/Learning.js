import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, MessageSquare, RefreshCw, Sparkles } from 'lucide-react';
import LearningPlan from './LearningPlan'; // Import the improved LearningPlan component

const Learning = ({ userEmail, jobContext, onClearJobContext }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activePlan, setActivePlan] = useState(null);
  const [activeJobContext, setActiveJobContext] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initial greeting
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 1,
        type: 'bot',
        content: `Hi! I'm your AI Learning Coach. I can help you create personalized learning plans, suggest projects, and answer questions about skill development. What would you like to work on today?`,
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  // Handle incoming job context to auto-start a plan
  useEffect(() => {
    if (jobContext) {
      const jobMessage = `Create a learning plan for the ${jobContext.title} position at ${jobContext.company}. I'm interested in this role and want to bridge the skill gaps.`;
      const userMessage = { id: Date.now(), type: 'user', content: jobMessage, timestamp: new Date() };

      setMessages(prev => [...prev, userMessage]);
      setActiveJobContext(jobContext);
      handleGeneratePlan(jobContext); // Directly call plan generation

      if (onClearJobContext) {
        onClearJobContext();
      }
    }
  }, [jobContext, onClearJobContext]);

  const handleGeneratePlan = async (job) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/generate-learning-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: userEmail,
          job_id: job.job_id,
          recommendation_id: job.recommendation_id
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate learning plan');
      }

      const data = await response.json();
      setActivePlan(data.learning_plan);
      // We no longer add the plan to the chat history
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `I encountered an error generating your learning plan: ${error.message}. Let me help you in another way - what specific skills would you like to focus on?`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = () => {
     if (!inputMessage.trim() || isLoading) return;
     // For simplicity, this is now a placeholder. The main functionality
     // is generating a plan from a job context.
     const userMessage = { id: Date.now(), type: 'user', content: inputMessage, timestamp: new Date() };
     setMessages(prev => [...prev, userMessage]);
     setInputMessage('');

     const botMessage = { id: Date.now() + 1, type: 'bot', content: "To generate a plan, please select a job from the 'Jobs' tab and click 'Get Learning Plan'.", timestamp: new Date() };
     setMessages(prev => [...prev, botMessage]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Main View: either show the Learning Plan or the Chat
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

  // Chat Interface
  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRadius: '20px',
      border: '1px solid rgba(255,255,255,0.2)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
      height: '80vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-blue-600" />
              AI Learning Coach
          </h1>
          <p className="text-gray-600 text-sm mt-1">
              Get personalized learning plans and career guidance
          </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.type === 'bot' && (
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={`max-w-[80%] ${message.type === 'user' ? 'order-first' : ''}`}>
              <div className={`rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.isError
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-gray-100'
              }`}>
                <div className="whitespace-pre-wrap text-sm leading-relaxed" style={{color: message.isError ? '#991B1B' : 'inherit'}}>
                  {message.content}
                </div>
              </div>
              <div className={`text-xs text-gray-500 mt-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
            {message.type === 'user' && (
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-sm">Generating your plan...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 border-t border-gray-200">
        <div className="flex gap-3">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question or select a job to create a plan..."
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="1"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center justify-center ${
              inputMessage.trim() && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Learning;