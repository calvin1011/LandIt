import React from 'react';
import { render, waitFor, screen } from '@testing-library/react';
import App from './App';

const mockUnsubscribe = jest.fn();
jest.mock('firebase/auth', () => ({
  onAuthStateChanged: jest.fn((auth, callback) => {
    callback(null);
    return mockUnsubscribe;
  })
}));

jest.mock('./firebase', () => ({
  auth: {
    signOut: jest.fn().mockResolvedValue(undefined),
    currentUser: null
  },
  isFirebaseConfigured: jest.fn(() => true)
}));

jest.mock('./components/Login', () => {
  return function MockLogin() {
    return <div data-testid="login-component">Login Component</div>;
  };
});

jest.mock('./components/ResumeUploader', () => {
  return function MockResumeUploader() {
    return <div data-testid="resume-uploader">Resume Uploader</div>;
  };
});

jest.mock('./components/JobRecommendations', () => {
  return function MockJobRecommendations() {
    return <div data-testid="job-recommendations">Job Recommendations</div>;
  };
});

jest.mock('./components/Profile', () => {
  return function MockProfile() {
    return <div data-testid="profile">Profile</div>;
  };
});

jest.mock('./components/AdminPanel', () => {
  return function MockAdminPanel() {
    return <div data-testid="admin-panel">Admin Panel</div>;
  };
});

jest.mock('./components/Learning', () => {
  return function MockLearning() {
    return <div data-testid="learning">Learning</div>;
  };
});

jest.mock('./components/SavedJobs', () => {
  return function MockSavedJobs() {
    return <div data-testid="saved-jobs">Saved Jobs</div>;
  };
});

test('renders app container', async () => {
  render(<App />);

  await waitFor(
    () => {
      const app = document.querySelector('.App');
      const login = screen.queryByTestId('login-component');
      const loading = screen.queryByText(/Checking authentication/);
      expect(app || login || loading).toBeTruthy();
    },
    { timeout: 2000 }
  );
});
