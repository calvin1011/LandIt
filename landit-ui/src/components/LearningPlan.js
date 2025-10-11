import React, { useState, useEffect } from 'react';
import { Clock, Target, TrendingUp, CheckCircle, AlertCircle, BookOpen, ExternalLink, Calendar, Star, Award, ChevronRight, ChevronDown, ArrowLeft } from 'lucide-react';

const LearningPlan = ({ userEmail, jobMatch, onBack, existingPlan }) => {
  const [learningPlan, setLearningPlan] = useState(existingPlan);
  const [expandedProject, setExpandedProject] = useState(null);
  const [activeTab, setActiveTab] = useState('critical');
  const [progress, setProgress] = useState({});

  useEffect(() => {
    if (existingPlan) {
      setLearningPlan(existingPlan);
    }
  }, [existingPlan]);

  const toggleProjectExpansion = (projectIndex, category) => {
    const key = `${category}-${projectIndex}`;
    setExpandedProject(expandedProject === key ? null : key);
  };

  const markMilestoneComplete = (projectKey, milestoneIndex, isComplete) => {
    setProgress(prev => {
      const newProgress = { ...prev };
      if (!newProgress[projectKey]) {
        newProgress[projectKey] = { milestones: {} };
      }
      newProgress[projectKey].milestones[milestoneIndex] = isComplete;
      return newProgress;
    });
  };

  const calculateProjectProgress = (project, projectKey) => {
    const projectProgress = progress[projectKey];
    if (!projectProgress?.milestones || !project.milestones) return 0;

    const totalMilestones = project.milestones.length;
    const completedMilestones = Object.values(projectProgress.milestones).filter(Boolean).length;

    return totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0;
  };

  const ProjectCard = ({ project, category, index }) => {
    const projectKey = `${category}-${index}`;
    const isExpanded = expandedProject === projectKey;
    const progressPercent = calculateProjectProgress(project, projectKey);

    const getDifficultyColor = (difficulty) => {
        switch (difficulty?.toLowerCase()) {
            case 'beginner': return 'text-green-600 bg-green-100 border-green-200';
            case 'intermediate': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
            case 'advanced': return 'text-red-600 bg-red-100 border-red-200';
            default: return 'text-gray-600 bg-gray-100 border-gray-200';
        }
    };

    const getCategoryStyles = (cat) => {
        switch (cat) {
            case 'critical': return { icon: <AlertCircle className="w-4 h-4 text-red-500" />, text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' };
            case 'important': return { icon: <Target className="w-4 h-4 text-orange-500" />, text: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' };
            case 'trending': return { icon: <TrendingUp className="w-4 h-4 text-blue-500" />, text: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' };
            default: return { icon: <BookOpen className="w-4 h-4 text-gray-500" />, text: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' };
        }
    };

    const categoryStyles = getCategoryStyles(category);

    return (
      <div className={`border ${categoryStyles.border} rounded-lg mb-4 overflow-hidden bg-white shadow-sm hover:shadow-lg transition-shadow duration-300`}>
        <div className="p-5 cursor-pointer" onClick={() => toggleProjectExpansion(index, category)}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {categoryStyles.icon}
                <h3 className="font-semibold text-lg text-gray-900">{project.title}</h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getDifficultyColor(project.difficulty)}`}>
                  {project.difficulty}
                </span>
              </div>
              <p className="text-gray-600 text-sm mb-3">{project.description}</p>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1.5"><Clock className="w-4 h-4" /><span>{project.estimated_weeks} weeks</span></div>
                <div className="flex items-center gap-1.5"><Star className="w-4 h-4" /><span>{project.skills_addressed?.length || 0} skills</span></div>
              </div>
              {progressPercent > 0 && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500 font-medium">Progress</span>
                    <span className="font-semibold text-blue-600">{Math.round(progressPercent)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5"><div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${progressPercent}%` }}></div></div>
                </div>
              )}
            </div>
            <div className="ml-4 pt-1">{isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}</div>
          </div>
        </div>
        {isExpanded && (
          <div className={`border-t ${categoryStyles.border} p-5 ${categoryStyles.bg}`}>
            <div className="grid md:grid-cols-2 gap-x-8 gap-y-6">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><Target className="w-4 h-4 text-gray-600" />Learning Outcomes</h4>
                <ul className="space-y-1.5">{project.learning_outcomes?.map((o, i) => <li key={i} className="text-sm text-gray-700 flex items-start gap-2"><CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />{o}</li>)}</ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2"><Calendar className="w-4 h-4 text-gray-600" />Milestones</h4>
                <div className="space-y-2.5">{project.milestones?.map((m, i) => (
                  <label key={i} className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" checked={!!progress[projectKey]?.milestones?.[i]} onChange={(e) => markMilestoneComplete(projectKey, i, e.target.checked)} className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                    <span className={`text-sm ${progress[projectKey]?.milestones?.[i] ? 'text-gray-500 line-through' : 'text-gray-700'}`}>{m}</span>
                  </label>
                ))}</div>
              </div>
              <div className="md:col-span-2">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><BookOpen className="w-4 h-4 text-gray-600" />Resources</h4>
                <div className="space-y-2">{project.resources?.map((r, i) => <div key={i} className="flex items-center gap-2 text-sm"><ExternalLink className="w-4 h-4 text-blue-500" /><span className="text-gray-600">{r.title || r}</span></div>)}</div>
              </div>
            </div>
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h5 className="font-semibold text-gray-800 mb-1">Portfolio Value</h5>
                    <p className="text-sm text-gray-600">{project.portfolio_value}</p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h5 className="font-semibold text-gray-800 mb-1">Market Relevance</h5>
                    <p className="text-sm text-gray-600">{project.market_relevance}</p>
                </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!learningPlan) {
    return (
        <div className="text-center p-12 text-gray-600">No learning plan available.</div>
    );
  }

  const projectCounts = {
    critical: learningPlan.critical_projects?.length || 0,
    important: learningPlan.important_projects?.length || 0,
    trending: learningPlan.trending_projects?.length || 0
  };

  return (
    <div style={{animation: 'fadeIn 0.5s ease-out'}}>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Your Learning Plan</h1>
            <p className="text-gray-600">For <span className="font-medium text-blue-600">{jobMatch.title}</span> at <span className="font-medium text-blue-600">{jobMatch.company}</span></p>
          </div>
          <button onClick={onBack} className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Coach
          </button>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6"><h2 className="text-xl font-semibold text-blue-900 mb-2">Strategic Overview</h2><p className="text-blue-800">{learningPlan.overview}</p></div>
      </div>

      <div className="mb-6 border-b border-gray-200"><nav className="flex space-x-6">
        {['critical', 'important', 'trending'].map(tab => (
          projectCounts[tab] > 0 &&
          <button key={tab} onClick={() => setActiveTab(tab)} className={`pb-2 px-1 border-b-2 font-medium text-sm capitalize ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {tab} Projects ({projectCounts[tab]})
          </button>
        ))}
      </nav></div>

      <div>
        {activeTab === 'critical' && learningPlan.critical_projects?.map((p, i) => <ProjectCard key={i} project={p} category="critical" index={i} />)}
        {activeTab === 'important' && learningPlan.important_projects?.map((p, i) => <ProjectCard key={i} project={p} category="important" index={i} />)}
        {activeTab === 'trending' && learningPlan.trending_projects?.map((p, i) => <ProjectCard key={i} project={p} category="trending" index={i} />)}
      </div>

      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Award className="w-5 h-5 text-gray-600" />Next Steps</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {learningPlan.next_steps?.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold shrink-0">{idx + 1}</div>
              <span className="text-gray-700 text-sm">{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearningPlan;