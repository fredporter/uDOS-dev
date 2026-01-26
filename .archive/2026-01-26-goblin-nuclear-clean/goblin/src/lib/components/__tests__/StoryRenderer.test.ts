import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import '@testing-library/jest-dom';
import StoryRenderer from '$lib/components/StoryRenderer.svelte';
import type { StoryState } from '$lib/types/story';

const MOCK_STORY: StoryState = {
  frontmatter: {
    title: 'Test Story',
    version: '1.0.0',
    description: 'A test story',
    author: 'Test Author',
    tags: [],
  },
  sections: [
    {
      index: 0,
      title: 'First Section',
      content: 'Welcome to the story',
      questions: [
        {
          name: 'username',
          label: 'What is your name?',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      index: 1,
      title: 'Second Section',
      content: 'Thanks for that information',
      questions: [
        {
          name: 'email',
          label: 'Email address',
          type: 'email',
          required: false,
        },
      ],
    },
  ],
  variables: {},
  answers: {},
  isComplete: false,
  currentSectionIndex: 0,
};

describe('StoryRenderer Component', () => {
  it('should render the story title', () => {
    const { container } = render(StoryRenderer, {
      props: { story: MOCK_STORY },
    });

    const title = container.querySelector('h1');
    expect(title?.textContent).toBe('Test Story');
  });

  it('should display the current section', () => {
    const { container } = container.querySelector('.section-indicator');
    // Verify section index display
  });

  it('should show progress bar when enabled', () => {
    const { container } = render(StoryRenderer, {
      props: { story: MOCK_STORY, showProgress: true },
    });

    const progressBar = container.querySelector('.progress-container');
    expect(progressBar).toBeTruthy();
  });

  it('should hide progress bar when disabled', () => {
    const { container } = render(StoryRenderer, {
      props: { story: MOCK_STORY, showProgress: false },
    });

    const progressBar = container.querySelector('.progress-container');
    expect(progressBar).toBeFalsy();
  });

  it('should enable submit button on last section', () => {
    const story: StoryState = {
      ...MOCK_STORY,
      currentSectionIndex: 1,
      answers: { email: 'test@example.com' },
    };

    const { container } = render(StoryRenderer, {
      props: { story },
    });

    const submitBtn = container.querySelector('.btn-primary');
    // Verify submit button is present (last section)
    expect(submitBtn?.textContent).toContain('Submit');
  });

  it('should call onSubmit with answers', async () => {
    let submittedAnswers: Record<string, any> | null = null;

    const handleSubmit = (answers: Record<string, any>) => {
      submittedAnswers = answers;
    };

    const story: StoryState = {
      ...MOCK_STORY,
      currentSectionIndex: 1,
      answers: { username: 'John', email: 'john@example.com' },
    };

    const { container } = render(StoryRenderer, {
      props: { story, onSubmit: handleSubmit },
    });

    // Note: Full integration test would click button and verify submission
    // This is a placeholder for the concept
  });

  it('should support light and dark themes', () => {
    const { container: lightContainer } = render(StoryRenderer, {
      props: { story: MOCK_STORY, theme: 'light' },
    });

    const darkContainer = render(StoryRenderer, {
      props: { story: MOCK_STORY, theme: 'dark' },
    });

    const lightRenderer = lightContainer.querySelector('.story-renderer');
    const darkRenderer = darkContainer.container.querySelector('.story-renderer');

    expect(lightRenderer?.classList.contains('dark')).toBe(false);
    expect(darkRenderer?.classList.contains('dark')).toBe(true);
  });
});
