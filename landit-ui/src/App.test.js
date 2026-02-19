import { render, waitFor } from '@testing-library/react';
import App from './App';

test('renders app container', async () => {
  render(<App />);
  await waitFor(() => {
    expect(document.querySelector('.App')).toBeInTheDocument();
  });
});
