import React, { useState, useEffect } from 'react';
import { Clock, Target, TrendingUp, CheckCircle, AlertCircle, BookOpen, ExternalLink, Calendar, Star, Award, ChevronRight, ChevronDown, Play, Pause, RotateCcw } from 'lucide-react';

const LearningPlan = ({ userEmail, jobMatch, onBack }) => {
  const [learningPlan, setLearningPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedProject, setExpandedProject] = useState(null);
  const [activeTab, setActiveTab] = useState('critical');
  const [progress, setProgress] = useState({});

  // Generate learning plan when component mounts
  useEffect(() => {
    if (jobMatch && userEmail) {
      generateLearningPlan();
    }
  }, [jobMatch, userEmail]);

  const generateLearningPlan = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/generate-learning-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: userEmail,
          job_id: jobMatch.job_id,
          recommendation_id: jobMatch.recommendation_id
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to generate learning plan: ${response.statusText}`);
      }

      const data = await response.json();
      setLearningPlan(data.learning_plan);
    } catch (err) {
      setError(err.message);
      console.error('Learning plan generation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateProgress = async (planId, progressData) => {
    try {
      await fetch(`http://localhost:8000/learning-plans/${planId}/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(progressData)
      });
    } catch (err) {
      console.error('Failed to update progress:', err);
    }
  };

  const toggleProjectExpansion = (projectIndex, category) => {
    const key = `${category}-${projectIndex}`;
    setExpandedProject(expandedProject === key ? null : key);
  };

  const markMilestoneComplete = (projectKey, milestoneIndex) => {
    setProgress(prev => ({
      ...prev,
      [projectKey]: {
        ...prev[projectKey],
        milestones: {
          ...prev[projectKey]?.milestones,
          [milestoneIndex]: !prev[projectKey]?.milestones?.[milestoneIndex]
        }
      }
    }));
  };

  const calculateProjectProgress = (projectKey) => {
    const projectProgress = progress[projectKey];
    if (!projectProgress?.milestones) return 0;

    const totalMilestones = Object.keys(projectProgress.milestones).length;
    const completedMilestones = Object.values(projectProgress.milestones).filter(Boolean).length;

    return totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0;
  };

  const ProjectCard = ({ project, category, index }) => {
    const projectKey = `${category}-${index}`;
    const isExpanded = expandedProject === projectKey;
    const progressPercent = calculateProjectProgress(projectKey);

    const getDifficultyColor = (difficulty) => {
      switch (difficulty?.toLowerCase()) {
        case 'beginner': return 'text-green-600 bg-green-100';
        case 'intermediate': return 'text-yellow-600 bg-yellow-100';
        case 'advanced': return 'text-red-600 bg-red-100';
        default: return 'text-gray-600 bg-gray-100';
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

    return (
      <div className="border border-gray-200 rounded-lg mb-4 overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
        <div
          className="p-4 cursor-pointer"
          onClick={() => toggleProjectExpansion(index, category)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {getCategoryIcon(category)}
                <h3 className="font-semibold text-lg text-gray-900">{project.title}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(project.difficulty)}`}>
                  {project.difficulty}
                </span>
              </div>

              <p className="text-gray-600 mb-3">{project.description}</p>

              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{project.estimated_weeks} weeks</span>
                </div>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4" />
                  <span>{project.skills_addressed?.length || 0} skills</span>
                </div>
              </div>

              {progressPercent > 0 && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Progress</span>
                    <span className="font-medium">{Math.round(progressPercent)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progressPercent}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>

            <div className="ml-4">
              {isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
            </div>
          </div>
        </div>

        {isExpanded && (
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Learning Outcomes
                </h4>
                <ul className="space-y-1 mb-4">
                  {project.learning_outcomes?.map((outcome, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {outcome}
                    </li>
                  ))}
                </ul>

                <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  Resources
                </h4>
                <div className="space-y-2">
                  {project.resources?.map((resource, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <ExternalLink className="w-4 h-4 text-blue-500" />
                      <span className="text-gray-600">{resource.title || resource}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Milestones
                </h4>
                <div className="space-y-2 mb-4">
                  {project.milestones?.map((milestone, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          markMilestoneComplete(projectKey, idx);
                        }}
                        className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                          progress[projectKey]?.milestones?.[idx] 
                            ? 'bg-green-500 border-green-500 text-white' 
                            : 'border-gray-300 hover:border-green-400'
                        }`}
                      >
                        {progress[projectKey]?.milestones?.[idx] && (
                          <CheckCircle className="w-3 h-3" />
                        )}
                      </button>
                      <span className={`text-sm ${
                        progress[projectKey]?.milestones?.[idx] 
                          ? 'text-gray-500 line-through' 
                          : 'text-gray-700'
                      }`}>
                        {milestone}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="bg-blue-50 p-3 rounded-lg">
                  <h5 className="font-medium text-blue-900 mb-1">Portfolio Value</h5>
                  <p className="text-sm text-blue-700">{project.portfolio_value}</p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="bg-green-50 p-3 rounded-lg">
                <h5 className="font-medium text-green-900 mb-1">Market Relevance</h5>
                <p className="text-sm text-green-700">{project.market_relevance}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Generating Your Learning Plan</h3>
          <p className="text-gray-600">Creating personalized project recommendations using AI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h3 className="text-lg font-medium text-red-900">Failed to Generate Learning Plan</h3>
          </div>
          <p className="text-red-700 mb-4">{error}</p>
          <div className="flex gap-3">
            <button
              onClick={generateLearningPlan}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!learningPlan) {
    return null;
  }

  const projectCounts = {
    critical: learningPlan.critical_projects?.length || 0,
    important: learningPlan.important_projects?.length || 0,
    trending: learningPlan.trending_projects?.length || 0
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Learning Plan</h1>
            <p className="text-gray-600">
              For <span className="font-medium">{jobMatch.title}</span> at <span className="font-medium">{jobMatch.company}</span>
            </p>
          </div>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Back to Jobs
          </button>
        </div>

        {/* Overview */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-blue-900 mb-3">Strategic Overview</h2>
          <p className="text-blue-800">{learningPlan.overview}</p>
        </div>

        {/* Timeline and Metrics */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Timeline
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Duration:</span>
                <span className="font-medium">{learningPlan.timeline?.total_duration_weeks} weeks</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Weekly Commitment:</span>
                <span className="font-medium">{learningPlan.timeline?.weekly_commitment}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5" />
              Success Metrics
            </h3>
            <ul className="space-y-2">
              {learningPlan.success_metrics?.slice(0, 3).map((metric, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  {metric}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Project Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('critical')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'critical'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Critical Projects ({projectCounts.critical})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('important')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'important'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Important Projects ({projectCounts.important})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('trending')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'trending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Trending Projects ({projectCounts.trending})
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Project Lists */}
      <div className="mb-8">
        {activeTab === 'critical' && (
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Critical Skills Projects</h2>
              <p className="text-gray-600">Start here - these projects address your most important skill gaps</p>
            </div>
            {learningPlan.critical_projects?.length > 0 ? (
              learningPlan.critical_projects.map((project, idx) => (
                <ProjectCard key={idx} project={project} category="critical" index={idx} />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No critical projects needed - you're well-qualified!
              </div>
            )}
          </div>
        )}

        {activeTab === 'important' && (
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Important Skills Projects</h2>
              <p className="text-gray-600">Build on your foundation with these valuable skills</p>
            </div>
            {learningPlan.important_projects?.length > 0 ? (
              learningPlan.important_projects.map((project, idx) => (
                <ProjectCard key={idx} project={project} category="important" index={idx} />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No important projects identified
              </div>
            )}
          </div>
        )}

        {activeTab === 'trending' && (
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Trending Skills Projects</h2>
              <p className="text-gray-600">Stay ahead of the curve with emerging technologies</p>
            </div>
            {learningPlan.trending_projects?.length > 0 ? (
              learningPlan.trending_projects.map((project, idx) => (
                <ProjectCard key={idx} project={project} category="trending" index={idx} />
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No trending projects identified
              </div>
            )}
          </div>
        )}
      </div>

      {/* Next Steps */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Play className="w-5 h-5" />
          Next Steps
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          {learningPlan.next_steps?.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                {idx + 1}
              </div>
              <span className="text-gray-700">{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearningPlan;