import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, MessageSquare, ChevronDown, ChevronRight, CheckCircle, Clock, Target, BookOpen, ExternalLink, TrendingUp, AlertCircle, Award, Calendar, Star, Zap } from 'lucide-react';

const Learning = ({ userEmail, jobContext, onClearJobContext }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [expandedProjects, setExpandedProjects] = useState({});
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
      }, 1500);
    }
  }, [messages.length]);

  const simulateTyping = (responseText, callback, isPlan = false) => {
    setIsTyping(true);

    const baseDelay = isPlan ? 50 : 30;
    const minDelay = isPlan ? 2000 : 1000;
    const maxDelay = isPlan ? 4000 : 3000;
    const calculatedDelay = Math.min(maxDelay, Math.max(minDelay, responseText.length * baseDelay));

    setTimeout(() => {
      callback();
      setIsTyping(false);
    }, calculatedDelay);
  };

  const handleGeneratePlan = useCallback(async (jobData) => {
    setIsLoading(true);

    if (!jobData || !jobData.job_id) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `I'm sorry, but I'm missing required information to generate this plan. Please try selecting the job again.`,
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

      // Create a rich learning plan message instead of redirecting
      const planMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `I've developed a personalized learning plan for the **${jobData.title}** position at **${jobData.company}**! Here's your customized roadmap:`,
        timestamp: new Date(),
        isPlan: true,
        learningPlan: data.learning_plan,
        jobContext: jobData
      };

      simulateTyping(planMessage.content, () => {
        setMessages(prev => [...prev, planMessage]);
      }, true);

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
  }, [userEmail]);

  useEffect(() => {
    if (jobContext) {
      console.log('Job Context received:', jobContext);

      const jobMessage = `Create a learning plan for the ${jobContext.title} position at ${jobContext.company}. I'm interested in this role and want to bridge the skill gaps.`;
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: jobMessage,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage]);
      handleGeneratePlan(jobContext);

      if (onClearJobContext) {
        onClearJobContext();
      }
    }
  }, [jobContext, onClearJobContext, handleGeneratePlan]);

  const toggleProjectExpansion = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  // Enhanced Learning Plan Component with Professional Formatting
  const LearningPlanMessage = ({ plan, jobContext }) => {
    const [activeTab, setActiveTab] = useState('critical');

    // Enhanced project card with better styling
    const ProjectCard = ({ project, category, index }) => {
      const projectId = `${category}-${index}`;
      const isExpanded = expandedProjects[projectId];

      const getDifficultyColor = (difficulty) => {
        switch (difficulty?.toLowerCase()) {
          case 'beginner': return {
            text: 'text-green-700',
            bg: 'bg-green-50',
            border: 'border-green-200',
            badge: 'text-green-800 bg-green-100 border-green-300'
          };
          case 'intermediate': return {
            text: 'text-yellow-700',
            bg: 'bg-yellow-50',
            border: 'border-yellow-200',
            badge: 'text-yellow-800 bg-yellow-100 border-yellow-300'
          };
          case 'advanced': return {
            text: 'text-red-700',
            bg: 'bg-red-50',
            border: 'border-red-200',
            badge: 'text-red-800 bg-red-100 border-red-300'
          };
          default: return {
            text: 'text-gray-700',
            bg: 'bg-gray-50',
            border: 'border-gray-200',
            badge: 'text-gray-800 bg-gray-100 border-gray-300'
          };
        }
      };

      const getCategoryConfig = (cat) => {
        switch (cat) {
          case 'critical':
            return {
              icon: <AlertCircle className="w-4 h-4 text-red-500" />,
              text: 'text-red-800',
              bg: 'bg-red-50',
              border: 'border-red-200',
              label: 'High Priority',
              gradient: 'from-red-500 to-orange-500'
            };
          case 'important':
            return {
              icon: <Target className="w-4 h-4 text-orange-500" />,
              text: 'text-orange-800',
              bg: 'bg-orange-50',
              border: 'border-orange-200',
              label: 'Core Skills',
              gradient: 'from-orange-500 to-amber-500'
            };
          case 'trending':
            return {
              icon: <TrendingUp className="w-4 h-4 text-blue-500" />,
              text: 'text-blue-800',
              bg: 'bg-blue-50',
              border: 'border-blue-200',
              label: 'Emerging Skills',
              gradient: 'from-blue-500 to-cyan-500'
            };
          default:
            return {
              icon: <BookOpen className="w-4 h-4 text-gray-500" />,
              text: 'text-gray-800',
              bg: 'bg-gray-50',
              border: 'border-gray-200',
              label: 'Additional Skills',
              gradient: 'from-gray-500 to-gray-600'
            };
        }
      };

      const difficultyColors = getDifficultyColor(project.difficulty);
      const categoryConfig = getCategoryConfig(category);

      return (
        <div className={`border ${categoryConfig.border} rounded-xl mb-4 overflow-hidden bg-white shadow-sm hover:shadow-lg transition-all duration-300`}>
          {/* Project Header */}
          <div
            className="p-5 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleProjectExpansion(projectId)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2 rounded-lg ${categoryConfig.bg}`}>
                    {categoryConfig.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h4 className="font-bold text-gray-900 text-base">{project.title}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${difficultyColors.badge}`}>
                        {project.difficulty}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${categoryConfig.bg} ${categoryConfig.text} border ${categoryConfig.border}`}>
                        {categoryConfig.label}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mt-2 leading-relaxed">{project.description}</p>
                  </div>
                </div>

                {/* Project Metadata */}
                <div className="flex items-center gap-6 text-sm text-gray-600 mt-3">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <span className="font-medium">{project.estimated_weeks} weeks</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4 text-gray-500" />
                    <span className="font-medium">{project.skills_addressed?.length || 0} key skills</span>
                  </div>
                  {project.portfolio_value && (
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-gray-500" />
                      <span className="font-medium text-blue-600">Portfolio-ready</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="ml-4 pt-2">
                {isExpanded ?
                  <ChevronDown className="w-5 h-5 text-gray-400" /> :
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                }
              </div>
            </div>
          </div>

          {/* Expanded Content */}
          {isExpanded && (
            <div className={`border-t ${categoryConfig.border} p-6 ${categoryConfig.bg}`}>
              <div className="grid md:grid-cols-2 gap-8">
                {/* Learning Outcomes */}
                <div>
                  <h5 className="font-bold text-gray-800 mb-4 flex items-center gap-2 text-sm uppercase tracking-wide">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    Learning Outcomes
                  </h5>
                  <ul className="space-y-3">
                    {project.learning_outcomes?.map((outcome, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-gray-700">
                        <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <CheckCircle className="w-3 h-3 text-green-600" />
                        </div>
                        <span className="leading-relaxed">{outcome}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Milestones */}
                <div>
                  <h5 className="font-bold text-gray-800 mb-4 flex items-center gap-2 text-sm uppercase tracking-wide">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    Project Milestones
                  </h5>
                  <div className="space-y-3">
                    {project.milestones?.map((milestone, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {i + 1}
                        </div>
                        <span className="text-sm text-gray-700 leading-relaxed">{milestone}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Resources */}
                {project.resources && project.resources.length > 0 && (
                  <div className="md:col-span-2">
                    <h5 className="font-bold text-gray-800 mb-4 flex items-center gap-2 text-sm uppercase tracking-wide">
                      <BookOpen className="w-4 h-4 text-purple-600" />
                      Learning Resources
                    </h5>
                    <div className="grid md:grid-cols-2 gap-3">
                      {project.resources.map((resource, i) => (
                        <a
                          key={i}
                          href={resource.url || '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 group"
                        >
                          <ExternalLink className="w-4 h-4 text-blue-500 group-hover:text-blue-600 flex-shrink-0" />
                          <span className="text-sm text-gray-700 group-hover:text-blue-600 font-medium">
                            {resource.title || resource}
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Value Metrics */}
                <div className="md:col-span-2 grid md:grid-cols-2 gap-4">
                  {project.portfolio_value && (
                    <div className="bg-white p-4 rounded-xl border border-gray-200">
                      <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                        <Award className="w-4 h-4 text-green-600" />
                        Portfolio Value
                      </h6>
                      <p className="text-sm text-gray-600">{project.portfolio_value}</p>
                    </div>
                  )}
                  {project.market_relevance && (
                    <div className="bg-white p-4 rounded-xl border border-gray-200">
                      <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-blue-600" />
                        Market Relevance
                      </h6>
                      <p className="text-sm text-gray-600">{project.market_relevance}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      );
    };

    const projectCounts = {
      critical: plan.critical_projects?.length || 0,
      important: plan.important_projects?.length || 0,
      trending: plan.trending_projects?.length || 0
    };

    // Enhanced tab configuration
    const tabConfig = {
      critical: { label: 'High Priority', count: projectCounts.critical },
      important: { label: 'Core Skills', count: projectCounts.important },
      trending: { label: 'Emerging Skills', count: projectCounts.trending }
    };

    return (
      <div className="bg-white rounded-2xl border border-gray-200 shadow-lg mt-4 max-w-4xl mx-auto">
        {/* Enhanced Plan Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-2xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Award className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900 text-lg">
                Learning Plan: {jobContext.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {jobContext.company} • Personalized Development Roadmap
              </p>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2 text-sm">
              <Zap className="w-4 h-4 text-yellow-500" />
              Strategic Overview
            </h4>
            <p className="text-gray-700 text-sm leading-relaxed">
              {plan.overview || `This personalized learning plan is designed to bridge key skill gaps and prepare you for the ${jobContext.title} role at ${jobContext.company}. Focus on hands-on projects that build both technical skills and portfolio value.`}
            </p>
          </div>
        </div>

        {/* Enhanced Navigation Tabs */}
        <div className="border-b border-gray-200 bg-gray-50">
          <nav className="flex px-6 -mb-px">
            {Object.entries(tabConfig).map(([tab, config]) => (
              config.count > 0 && (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-4 border-b-2 font-semibold text-sm transition-all duration-200 ${
                    activeTab === tab 
                      ? 'border-blue-500 text-blue-600 bg-white rounded-t-lg' 
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {config.label}
                  <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                    activeTab === tab 
                      ? 'bg-blue-100 text-blue-600' 
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {config.count}
                  </span>
                </button>
              )
            ))}
          </nav>
        </div>

        {/* Projects Section */}
        <div className="p-6 max-h-96 overflow-y-auto">
          {activeTab === 'critical' && plan.critical_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="critical" index={i} />
          ))}
          {activeTab === 'important' && plan.important_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="important" index={i} />
          ))}
          {activeTab === 'trending' && plan.trending_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="trending" index={i} />
          ))}

          {!plan[`${activeTab}_projects`]?.length && (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="font-medium">No projects in this category</p>
              <p className="text-sm">Focus on completing projects from other priority levels</p>
            </div>
          )}
        </div>

        {/* Enhanced Next Steps */}
        {plan.next_steps && plan.next_steps.length > 0 && (
          <div className="p-6 border-t border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
            <h4 className="font-bold text-gray-800 text-sm mb-4 flex items-center gap-2 uppercase tracking-wide">
              <Target className="w-4 h-4 text-green-600" />
              Recommended Next Steps
            </h4>
            <div className="grid md:grid-cols-2 gap-3">
              {plan.next_steps.map((step, i) => (
                <div key={i} className="flex items-start gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-all duration-200">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {i + 1}
                  </div>
                  <span className="text-gray-700 text-sm font-medium leading-relaxed">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: userEmail,
          message: inputMessage,
          conversation_history: messages
            .filter(m => m.type === 'user' || m.type === 'bot')
            .slice(-6) // Last 6 messages for context
            .map(m => ({
              role: m.type === 'user' ? 'user' : 'assistant',
              content: m.content
            }))
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.response,
        timestamp: new Date()
      };

      simulateTyping(botMessage.content, () => {
        setMessages(prev => [...prev, botMessage]);
      });

    } catch (error) {
      console.error('Chat error:', error);

      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "I'm having trouble connecting to my AI service right now. Please try again in a moment, or use the 'Get Learning Plan' feature for structured guidance.",
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

  const handleQuickAction = (action) => {
    if (isLoading || isTyping) return;
    setInputMessage(action);
    setTimeout(() => sendMessage(), 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

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
            <div style={{ width: '8px', height: '8px', backgroundColor: '#667eea', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out both' }}></div>
            <div style={{ width: '8px', height: '8px', backgroundColor: '#667eea', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out both', animationDelay: '0.16s' }}></div>
            <div style={{ width: '8px', height: '8px', backgroundColor: '#667eea', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out both', animationDelay: '0.32s' }}></div>
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

            <div style={{ maxWidth: '70%' }}>
              <div style={{
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

              {/* Render Learning Plan if this message contains one */}
              {message.isPlan && message.learningPlan && (
                <LearningPlanMessage
                  plan={message.learningPlan}
                  jobContext={message.jobContext}
                />
              )}
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