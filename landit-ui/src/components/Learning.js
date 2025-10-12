import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, MessageSquare, ChevronDown, ChevronRight, CheckCircle, Clock, Target, BookOpen, ExternalLink, TrendingUp, AlertCircle, Award } from 'lucide-react';

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
  }, [jobContext, onClearJobContext]);

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

  const handleGeneratePlan = async (jobData) => {
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
        content: `I've created a personalized learning plan for the ${jobData.title} position at ${jobData.company}! Here's your customized roadmap:`,
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
  };

  const toggleProjectExpansion = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  // Learning Plan Component (rendered within chat)
  const LearningPlanMessage = ({ plan, jobContext }) => {
    const [activeTab, setActiveTab] = useState('critical');

    const ProjectCard = ({ project, category, index }) => {
      const projectId = `${category}-${index}`;
      const isExpanded = expandedProjects[projectId];

      const getDifficultyColor = (difficulty) => {
        switch (difficulty?.toLowerCase()) {
          case 'beginner': return { text: 'text-green-700', bg: 'bg-green-100', border: 'border-green-200' };
          case 'intermediate': return { text: 'text-yellow-700', bg: 'bg-yellow-100', border: 'border-yellow-200' };
          case 'advanced': return { text: 'text-red-700', bg: 'bg-red-100', border: 'border-red-200' };
          default: return { text: 'text-gray-700', bg: 'bg-gray-100', border: 'border-gray-200' };
        }
      };

      const getCategoryIcon = (cat) => {
        switch (cat) {
          case 'critical': return <AlertCircle className="w-4 h-4 text-red-500" />;
          case 'important': return <Target className="w-4 h-4 text-orange-500" />;
          case 'trending': return <TrendingUp className="w-4 h-4 text-blue-500" />;
          default: return <BookOpen className="w-4 h-4 text-gray-500" />;
        }
      };

      const difficultyColors = getDifficultyColor(project.difficulty);

      return (
        <div className={`border ${difficultyColors.border} rounded-lg mb-3 overflow-hidden bg-white shadow-sm`}>
          <div
            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleProjectExpansion(projectId)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getCategoryIcon(category)}
                  <h4 className="font-semibold text-gray-900 text-sm">{project.title}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${difficultyColors.border} ${difficultyColors.bg} ${difficultyColors.text}`}>
                    {project.difficulty}
                  </span>
                </div>
                <p className="text-gray-600 text-xs mb-2">{project.description}</p>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{project.estimated_weeks} weeks</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    <span>{project.skills_addressed?.length || 0} skills</span>
                  </div>
                </div>
              </div>
              <div className="ml-2 pt-1">
                {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
              </div>
            </div>
          </div>

          {isExpanded && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <h5 className="font-semibold text-gray-800 text-xs mb-2 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3 text-green-600" />
                    Learning Outcomes
                  </h5>
                  <ul className="space-y-1 text-xs text-gray-700">
                    {project.learning_outcomes?.map((outcome, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-green-500 mt-0.5">•</span>
                        {outcome}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h5 className="font-semibold text-gray-800 text-xs mb-2 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-blue-600" />
                    Milestones
                  </h5>
                  <div className="space-y-1 text-xs text-gray-700">
                    {project.milestones?.map((milestone, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full border border-gray-300 flex items-center justify-center">
                          <div className="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
                        </div>
                        {milestone}
                      </div>
                    ))}
                  </div>
                </div>

                {project.resources && project.resources.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-800 text-xs mb-2 flex items-center gap-1">
                      <ExternalLink className="w-3 h-3 text-purple-600" />
                      Resources
                    </h5>
                    <div className="space-y-1 text-xs">
                      {project.resources.map((resource, i) => (
                        <div key={i} className="flex items-center gap-1 text-blue-600 hover:text-blue-800 cursor-pointer">
                          <ExternalLink className="w-3 h-3" />
                          <span>{resource.title || resource}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(project.portfolio_value || project.market_relevance) && (
                  <div className="grid grid-cols-2 gap-2">
                    {project.portfolio_value && (
                      <div className="bg-white p-2 rounded border border-gray-200">
                        <h6 className="font-semibold text-gray-800 text-xs">Portfolio Value</h6>
                        <p className="text-gray-600 text-xs">{project.portfolio_value}</p>
                      </div>
                    )}
                    {project.market_relevance && (
                      <div className="bg-white p-2 rounded border border-gray-200">
                        <h6 className="font-semibold text-gray-800 text-xs">Market Relevance</h6>
                        <p className="text-gray-600 text-xs">{project.market_relevance}</p>
                      </div>
                    )}
                  </div>
                )}
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

    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm mt-2 max-w-2xl">
        {/* Plan Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Award className="w-4 h-4 text-blue-600" />
            <h3 className="font-bold text-gray-900 text-sm">
              Learning Plan: {jobContext.title} at {jobContext.company}
            </h3>
          </div>
          <p className="text-gray-600 text-xs">{plan.overview}</p>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex px-4 -mb-px">
            {['critical', 'important', 'trending'].map(tab => (
              projectCounts[tab] > 0 && (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-2 px-3 border-b-2 font-medium text-xs capitalize ${
                    activeTab === tab 
                      ? 'border-blue-500 text-blue-600' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab} ({projectCounts[tab]})
                </button>
              )
            ))}
          </nav>
        </div>

        {/* Projects */}
        <div className="p-4 max-h-96 overflow-y-auto">
          {activeTab === 'critical' && plan.critical_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="critical" index={i} />
          ))}
          {activeTab === 'important' && plan.important_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="important" index={i} />
          ))}
          {activeTab === 'trending' && plan.trending_projects?.map((project, i) => (
            <ProjectCard key={i} project={project} category="trending" index={i} />
          ))}
        </div>

        {/* Next Steps */}
        {plan.next_steps && plan.next_steps.length > 0 && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <h4 className="font-semibold text-gray-800 text-xs mb-2 flex items-center gap-1">
              <Target className="w-3 h-3 text-green-600" />
              Next Steps
            </h4>
            <div className="space-y-1 text-xs text-gray-700">
              {plan.next_steps.map((step, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="w-4 h-4 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </span>
                  {step}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
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

    setIsTyping(true);
    setTimeout(() => {
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "I'd be happy to help! To create a personalized learning plan, please select a job from the 'Jobs' tab and click 'Get Learning Plan'. I can then analyze the role and build a customized roadmap for you.",
        timestamp: new Date()
      };

      simulateTyping(botMessage.content, () => {
        setMessages(prev => [...prev, botMessage]);
      });
    }, 800);
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