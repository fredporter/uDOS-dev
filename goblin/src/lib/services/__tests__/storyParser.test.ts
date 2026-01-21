import { describe, it, expect } from 'vitest';
import {
  parseStoryFile,
  parseSection,
  extractStoryBlocks,
  parseStoryBlock,
  renderMarkdown,
  getProgress,
} from '$lib/services/storyParser';

const SAMPLE_STORY = `---
title: Test Story
version: 1.0.0
description: A test story
author: Test Author
---

# First Section

This is the first section.

\`\`\`story
{
  "name": "username",
  "label": "What's your name?",
  "type": "text",
  "required": true
}
\`\`\`

## Second Section

Here's another question.

\`\`\`story
{
  "name": "email",
  "label": "Email",
  "type": "email",
  "required": false
}
\`\`\`

---

const testVariable = "test";
`;

describe('storyParser', () => {
  describe('parseStoryFile', () => {
    it('should parse complete story file', () => {
      const result = parseStoryFile(SAMPLE_STORY);

      expect(result.frontmatter.title).toBe('Test Story');
      expect(result.frontmatter.version).toBe('1.0.0');
      expect(result.frontmatter.description).toBe('A test story');
      expect(result.sections.length).toBeGreaterThan(0);
      expect(result.answers).toEqual({});
      expect(result.isComplete).toBe(false);
      expect(result.currentSectionIndex).toBe(0);
    });

    it('should handle missing frontmatter gracefully', () => {
      const story = '# Section\n\nContent';
      const result = parseStoryFile(story);

      expect(result.frontmatter.title).toBe('Untitled Story');
      expect(result.frontmatter.version).toBe('1.0.0');
      expect(result.sections.length).toBeGreaterThan(0);
    });
  });

  describe('extractStoryBlocks', () => {
    it('should extract story blocks from markdown', () => {
      const text = `
Some text

\`\`\`story
{"name": "field1", "label": "Field 1", "type": "text"}
\`\`\`

More text

\`\`\`story
{"name": "field2", "label": "Field 2", "type": "email"}
\`\`\`
`;

      const blocks = extractStoryBlocks(text);
      expect(blocks).toHaveLength(2);
      expect(blocks[0]).toContain('field1');
      expect(blocks[1]).toContain('field2');
    });

    it('should return empty array when no blocks found', () => {
      const text = 'Just some markdown\n\nNo story blocks here';
      const blocks = extractStoryBlocks(text);
      expect(blocks).toHaveLength(0);
    });
  });

  describe('parseStoryBlock', () => {
    it('should parse valid story block YAML', () => {
      const yaml = `{
  "name": "username",
  "label": "Username",
  "type": "text",
  "required": true,
  "placeholder": "Enter username"
}`;

      const result = parseStoryBlock(yaml);
      expect(result.name).toBe('username');
      expect(result.label).toBe('Username');
      expect(result.type).toBe('text');
      expect(result.required).toBe(true);
      expect(result.placeholder).toBe('Enter username');
    });

    it('should handle missing optional fields', () => {
      const yaml = `{
  "name": "email",
  "label": "Email",
  "type": "email"
}`;

      const result = parseStoryBlock(yaml);
      expect(result.name).toBe('email');
      expect(result.required).toBe(false); // default
      expect(result.placeholder).toBeUndefined();
    });

    it('should handle malformed JSON', () => {
      const yaml = 'invalid json {';
      expect(() => parseStoryBlock(yaml)).toThrow();
    });
  });

  describe('renderMarkdown', () => {
    it('should render markdown to HTML', () => {
      const md = '# Heading\n\nParagraph **bold** text.';
      const html = renderMarkdown(md);

      expect(html).toContain('<h1>');
      expect(html).toContain('Heading');
      expect(html).toContain('<strong>');
      expect(html).toContain('bold');
    });

    it('should remove story blocks before rendering', () => {
      const md = `Paragraph

\`\`\`story
{"name": "field", "label": "Field"}
\`\`\`

More content`;

      const html = renderMarkdown(md);
      expect(html).toContain('Paragraph');
      expect(html).toContain('More content');
      expect(html).not.toContain('story');
      expect(html).not.toContain('field');
    });
  });

  describe('getProgress', () => {
    it('should calculate progress percentage', () => {
      expect(getProgress(0, 5)).toBe(0);
      expect(getProgress(2, 5)).toBe(40);
      expect(getProgress(4, 5)).toBe(80);
      expect(getProgress(5, 5)).toBe(100);
    });

    it('should handle edge cases', () => {
      expect(getProgress(0, 1)).toBe(0);
      expect(getProgress(1, 1)).toBe(100);
      expect(getProgress(0, 0)).toBe(100); // edge case
    });

    it('should round to nearest integer', () => {
      expect(getProgress(1, 3)).toBe(33); // 33.33... → 33
      expect(getProgress(2, 3)).toBe(67); // 66.66... → 67
    });
  });

  describe('parseSection', () => {
    it('should parse section with questions', () => {
      const text = `# Section Title

This is the content.

\`\`\`story
{"name": "q1", "label": "Question 1", "type": "text"}
\`\`\``;

      const section = parseSection(text, 0, {});
      expect(section.title).toBe('Section Title');
      expect(section.content).toContain('This is the content');
      expect(section.questions.length).toBe(1);
      expect(section.questions[0].name).toBe('q1');
    });

    it('should handle sections without questions', () => {
      const text = `# Intro Section

Just informational content, no form fields.`;

      const section = parseSection(text, 0, {});
      expect(section.title).toBe('Intro Section');
      expect(section.questions.length).toBe(0);
    });
  });
});
