import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Clock, Target, TrendingUp, CheckCircle, AlertCircle, BookOpen, Sparkles, MessageSquare, RefreshCw } from 'lucide-react';

const Learning = ({ userEmail }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initial greeting when component loads
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 1,
        type: 'bot',
        content: `Hi! I'm your AI Learning Coach. I can help you create personalized learning plans, suggest projects, and answer questions about skill development.

To get started, you can:
• Ask me to create a learning plan for a specific job
• Request project recommendations for certain skills
• Get advice on career development
• Modify existing learning plans

What would you like to work on today?`,
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Determine the type of request and call appropriate endpoint
      const response = await handleChatMessage(inputMessage);

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.content,
        learningPlan: response.learningPlan,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      if (response.learningPlan) {
        setCurrentPlan(response.learningPlan);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `I'm sorry, I encountered an error: ${error.message}. Please try rephrasing your request or ask something else.`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatMessage = async (message) => {
    const messageLower = message.toLowerCase();

    // Check if user is asking for a learning plan
    if (messageLower.includes('learning plan') || messageLower.includes('create plan') || messageLower.includes('skill gap')) {
      return await generateLearningPlanFromChat(message);
    }

    // Check if user is asking about projects
    if (messageLower.includes('project') || messageLower.includes('build') || messageLower.includes('portfolio')) {
      return await generateProjectSuggestions(message);
    }

    // General chat/advice
    return await getGeneralAdvice(message);
  };

  const generateLearningPlanFromChat = async (message) => {
    // For now, we'll simulate generating a plan
    // In production, you'd call your learning plan API with the chat context
    try {
      const response = await fetch('http://localhost:8000/chat/learning-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: userEmail,
          message: message,
          context: currentPlan ? 'has_existing_plan' : 'new_plan'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate learning plan');
      }

      const data = await response.json();
      return {
        content: data.message,
        learningPlan: data.learning_plan
      };
    } catch (error) {
      // Fallback response
      return {
        content: `I'd love to help you create a learning plan! However, I need a bit more information:

1. What specific job role are you targeting?
2. What are your current skills?
3. Are there particular technologies you want to learn?

You can also get job recommendations first, then I can create a targeted learning plan based on specific job requirements.`
      };
    }
  };

  const generateProjectSuggestions = async (message) => {
    try {
      const response = await fetch('http://localhost:8000/chat/project-suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: userEmail,
          message: message,
          current_plan: currentPlan
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get project suggestions');
      }

      const data = await response.json();
      return { content: data.message };
    } catch (error) {
      return {
        content: `I can suggest some great project ideas! Here are a few general recommendations:

**Beginner Projects:**
• Personal portfolio website
• Todo list application
• Simple blog or content management system

**Intermediate Projects:**
• E-commerce application with payment integration
• Real-time chat application
• API-driven dashboard with data visualization

**Advanced Projects:**
• Microservices architecture implementation
• Machine learning model deployment
• Full-stack application with advanced features

What specific technologies or skills would you like to focus on?`
      };
    }
  };

  const getGeneralAdvice = async (message) => {
    try {
      const response = await fetch('http://localhost:8000/chat/advice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: userEmail,
          message: message,
          context: {
            current_plan: currentPlan,
            conversation_history: messages.slice(-5) // Last 5 messages for context
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get advice');
      }

      const data = await response.json();
      return { content: data.message };
    } catch (error) {
      return {
        content: `I'm here to help with your learning journey! I can assist with:

• Creating personalized learning plans
• Suggesting portfolio projects
• Career development advice
• Skill gap analysis
• Technology recommendations

What specific aspect of your learning or career development would you like to discuss?`
      };
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const LearningPlanDisplay = ({ plan }) => {
    if (!plan) return null;

    return (
      <div className="mt-4 border border-blue-200 rounded-lg p-4 bg-blue-50">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          Generated Learning Plan
        </h3>

        <div className="space-y-3">
          <div className="bg-white rounded p-3">
            <h4 className="font-medium text-gray-900 mb-2">Overview</h4>
            <p className="text-sm text-gray-700">{plan.overview}</p>
          </div>

          {plan.critical_projects && plan.critical_projects.length > 0 && (
            <div className="bg-white rounded p-3">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                Critical Projects ({plan.critical_projects.length})
              </h4>
              <div className="space-y-2">
                {plan.critical_projects.slice(0, 2).map((project, idx) => (
                  <div key={idx} className="border-l-2 border-red-200 pl-3">
                    <h5 className="font-medium text-sm">{project.title}</h5>
                    <p className="text-xs text-gray-600">{project.description}</p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {project.estimated_weeks} weeks
                      </span>
                      <span>{project.difficulty}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white rounded p-3">
            <h4 className="font-medium text-gray-900 mb-2">Timeline</h4>
            <div className="text-sm text-gray-700">
              <p><strong>Duration:</strong> {plan.timeline?.total_duration_weeks} weeks</p>
              <p><strong>Commitment:</strong> {plan.timeline?.weekly_commitment}</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const MessageBubble = ({ message }) => (
    <div className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
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
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </div>

          {message.learningPlan && (
            <LearningPlanDisplay plan={message.learningPlan} />
          )}
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
  );

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
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-blue-600" />
              AI Learning Coach
            </h1>
            <p className="text-gray-600 text-sm mt-1">
              Get personalized learning plans and career guidance
            </p>
          </div>

          {currentPlan && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Active Plan</p>
              <p className="text-sm font-medium text-blue-600">
                {currentPlan.timeline?.total_duration_weeks} weeks • {currentPlan.metadata?.target_job}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about learning plans, projects, or career advice..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="2"
              disabled={isLoading}
            />
          </div>

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

        <div className="flex flex-wrap gap-2 mt-3">
          <button
            onClick={() => setInputMessage("Create a learning plan for a software engineer role")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
            disabled={isLoading}
          >
            📚 Create Learning Plan
          </button>
          <button
            onClick={() => setInputMessage("Suggest portfolio projects for web development")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
            disabled={isLoading}
          >
            💼 Portfolio Projects
          </button>
          <button
            onClick={() => setInputMessage("How can I improve my technical skills?")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
            disabled={isLoading}
          >
            🚀 Career Advice
          </button>
        </div>
      </div>
    </div>
  );
};

export default Learning;