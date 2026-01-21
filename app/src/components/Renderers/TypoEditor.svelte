<script lang="ts">
  import { confirm } from "@tauri-apps/plugin-dialog";
  import {
    Open,
    Save,
    Copy,
    Eye,
    Bullet,
    Blockquote,
    Link,
    Image,
    Table,
    CodeBracket,
    Slideshow,
    Document,
  } from "../icons";

  export let isDark: boolean = false;
  export let onDarkModeToggle: () => void = () => {};
  export let onSave: (content: string) => void = () => {};
  export let onNew: () => void = () => {};
  export let onOpen: () => void = () => {};
  export let currentFile: string = "";

  // Export content and setters for parent component
  export function getContent(): string {
    return content;
  }

  export function setContent(newContent: string): void {
    content = newContent;
  }

  let content: string = `# Welcome to Markdown

Get started with markdown!

Markdown is open source and distributed under the MIT License. Leave feedback, contribute, or fork the project on GitHub.

## View

Content can be viewed as a document or slideshow, separate slides with an hr tag (---).

## Format

Automatically format content with Prettier using the format button or CTRL + S.

## Save

When a file is opened or saved, all future changes are saved automatically.

Files are stored directly on the local computer, not in an online storage system.

## Execute Code

JavaScript and TypeScript code blocks can be executed in the browser by clicking the block.

\`\`\`ts
function clickHere(): string {
	return "Hello world!";
}

clickHere();
\`\`\`

## Keyboard Shortcuts

| Function | Key Combination |
| --- | --- |
| Focus text area | i |
| Toggle view mode | ESC |
| Format | CTRL + S |
| Anchor | CTRL + [ |
| Image | CTRL + ] |
| Table | CTRL + \\\\ |`;

  export let viewMode: boolean = false;
  export let wordCount: number = 0;
  export let charCount: number = 0;

  let editorTextarea: HTMLTextAreaElement;
  let previewDiv: HTMLDivElement;

  $: {
    wordCount = content.split(/\s+/).filter((w) => w.length > 0).length;
    charCount = content.length;
  }

  function syncScroll() {
    if (editorTextarea && previewDiv) {
      const scrollPercentage =
        editorTextarea.scrollTop /
        (editorTextarea.scrollHeight - editorTextarea.clientHeight);
      previewDiv.scrollTop =
        scrollPercentage * (previewDiv.scrollHeight - previewDiv.clientHeight);
    }
  }

  function handleSave() {
    onSave(content);
  }

  async function handleNew() {
    const confirmed = await confirm(
      "Create new file? Unsaved changes will be lost.",
      {
        title: "New File",
        kind: "warning",
      },
    );
    if (confirmed) {
      onNew();
    }
  }

  function handleOpen() {
    onOpen();
  }

  function toggleView() {
    viewMode = !viewMode;
  }

  function renderMarkdown(text: string): string {
    let lines = text.split("\n");
    let output: string[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let inTable = false;
    let tableRows: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.startsWith("```")) {
        if (inCodeBlock) {
          output.push(`<pre><code>${codeBlockContent.join("\n")}</code></pre>`);
          codeBlockContent = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      if (line.includes("|")) {
        if (!inTable) {
          inTable = true;
          tableRows = [];
        }
        const cells = line.split("|").slice(1, -1);
        const isHeader = i + 1 < lines.length && lines[i + 1].includes("---");
        const tag = isHeader ? "th" : "td";
        const row = `<tr>${cells.map((cell) => `<${tag}>${cell.trim()}</${tag}>`).join("")}</tr>`;
        tableRows.push(row);
        if (isHeader) i++;
      } else {
        if (inTable) {
          output.push(`<table><tbody>${tableRows.join("")}</tbody></table>`);
          inTable = false;
          tableRows = [];
        }

        if (line.startsWith("# ")) output.push(`<h1>${line.substring(2)}</h1>`);
        else if (line.startsWith("## "))
          output.push(`<h2>${line.substring(3)}</h2>`);
        else if (line.startsWith("### "))
          output.push(`<h3>${line.substring(4)}</h3>`);
        else if (line.startsWith("- "))
          output.push(`<li>${line.substring(2)}</li>`);
        else if (line.startsWith("> "))
          output.push(`<blockquote>${line.substring(2)}</blockquote>`);
        else if (line.trim() === "") output.push(`<br />`);
        else output.push(`<p>${line}</p>`);
      }
    }

    if (inCodeBlock) {
      output.push(`<pre><code>${codeBlockContent.join("\n")}</code></pre>`);
    }
    if (inTable) {
      output.push(`<table><tbody>${tableRows.join("")}</tbody></table>`);
    }

    return output.join("");
  }
</script>

<div
  class="flex flex-col {isDark
    ? 'bg-gray-950 text-gray-50'
    : 'bg-white text-gray-900'} selection:bg-gray-400/40"
  style="height: calc(100dvh - var(--typo-bottom-bar-height, 44px));"
>
  <!-- Top Header -->
  {#if !viewMode}
    <header class="flex justify-between p-2 text-sm">
      <nav class="flex w-full items-center justify-between sm:w-fit">
        <div class="flex">
          <button title="New" class="button" on:click={handleNew}>
            <Document class="w-5 h-5" />
            <span class="hidden lg:inline">New</span>
          </button>
          <button title="Open" class="button" on:click={handleOpen}>
            <Open class="w-5 h-5" />
            <span class="hidden lg:inline">Open</span>
          </button>
          <button title="Save" class="button" on:click={handleSave}>
            <Save class="w-5 h-5" />
            <span class="hidden lg:inline">Save</span>
          </button>
          <button
            title="Copy"
            class="button"
            on:click={() => navigator.clipboard.writeText(content)}
          >
            <Copy class="w-5 h-5" />
            <span class="hidden lg:inline">Copy</span>
          </button>
          <button title="View" class="button lg:hidden" on:click={toggleView}>
            <Eye class="w-5 h-5" />
          </button>
        </div>
      </nav>
    </header>
  {/if}

  <!-- Main Content -->
  <main
    class="grid flex-1 overflow-hidden {!viewMode && 'lg:grid-cols-2'}"
    style="font-family: var(--typo-font-family, 'Atkinson Hyperlegible'), sans-serif; font-size: var(--typo-font-size, 1em);"
  >
    {#if !viewMode}
      <!-- Editor -->
      <div class="flex flex-col overflow-hidden min-h-0 h-full">
        <textarea
          bind:this={editorTextarea}
          bind:value={content}
          on:scroll={syncScroll}
          on:keyup={syncScroll}
          class="flex-1 resize-none appearance-none overflow-y-auto p-5 font-mono text-sm leading-relaxed transition placeholder:text-gray-400 focus:outline-none {isDark
            ? 'bg-gray-900 text-gray-50'
            : 'bg-gray-50 text-gray-900'}"
          style="font-family: var(--typo-font-family, 'Atkinson Hyperlegible'), monospace; font-size: var(--typo-font-size, 1em);"
          placeholder="# Title"
        />
        <!-- Formatting Toolbar -->
        <div
          class="flex flex-wrap gap-1 p-2 w-full shrink-0 {isDark
            ? 'bg-gray-900 border-gray-800'
            : 'bg-gray-100 border-gray-200'} border-t"
        >
          <button class="button" title="Heading">H</button>
          <button class="button" title="Bullet"><Bullet /></button>
          <button class="button" title="Blockquote"><Blockquote /></button>
          <button class="button italic" title="Italic">I</button>
          <button class="button font-bold" title="Bold">B</button>
          <button class="button" title="Anchor"><Link /></button>
          <button class="button" title="Image"><Image /></button>
          <button class="button" title="Table"><Table /></button>
          <button class="button" title="Code"
            ><CodeBracket className="" /></button
          >
          <button class="button" title="Slide"><Slideshow /></button>
        </div>
      </div>
    {/if}

    <!-- Preview -->
    <div
      class="{viewMode
        ? 'flex'
        : 'hidden lg:flex'} h-full flex-col overflow-hidden"
      style="view-transition-name: preview;"
    >
      <div
        bind:this={previewDiv}
        class="grow overflow-y-auto {isDark ? 'bg-gray-950' : 'bg-white'}"
      >
        <div
          class="prose {isDark ? 'prose-invert' : ''} mx-auto max-w-[72ch] p-8"
          style="font-family: var(--typo-font-family, 'Atkinson Hyperlegible'), sans-serif; font-size: var(--typo-font-size, 1em);"
        >
          {@html renderMarkdown(content)}
        </div>
      </div>
    </div>
  </main>
</div>

<style lang="postcss">
  textarea {
    padding: 1.25rem !important;
  }

  .prose {
    padding: 0.5rem 2rem 2rem 2rem !important;
  }

  :global(.button) {
    display: flex;
    min-width: 2.5rem;
    min-height: 2.5rem;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    border-radius: 0.5rem;
    padding: 0.5rem;
    line-height: 1;
    font-weight: 600;
    letter-spacing: 0.025em;
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 150ms;
    transform: scale(1);
  }

  :global(.button:hover:not(:disabled)) {
    transform: scale(1.03);
  }

  :global(html:not(.dark) .button:hover:not(:disabled)) {
    background-color: rgba(59, 130, 246, 0.1);
  }

  :global(html.dark .button:hover:not(:disabled)) {
    background-color: rgba(107, 114, 128, 0.2);
  }

  :global(.button:active:not(:disabled)) {
    transform: scale(0.95);
  }

  :global(html:not(.dark) .button:active:not(:disabled)) {
    background-color: rgba(59, 130, 246, 0.2);
  }

  :global(html.dark .button:active:not(:disabled)) {
    background-color: rgba(107, 114, 128, 0.3);
  }

  :global(.button:disabled) {
    cursor: not-allowed;
    color: rgb(156, 163, 175);
  }

  :global(.button:disabled:hover) {
    background-color: transparent;
  }

  :global(.prose h1) {
    font-size: 1.875rem;
    font-weight: bold;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
  }

  :global(.prose h2) {
    font-size: 1.5rem;
    font-weight: bold;
    margin-top: 1.25rem;
    margin-bottom: 0.75rem;
  }

  :global(.prose h3) {
    font-size: 1.25rem;
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  :global(.prose p) {
    margin: 0.5rem 0;
    line-height: 1.5;
  }

  :global(.prose li) {
    margin-left: 1rem;
    list-style-type: disc;
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
  }

  :global(.prose blockquote) {
    border-left: 4px solid;
    padding-left: 1rem;
    font-style: italic;
    margin: 0.5rem 0;
  }

  :global(.prose pre) {
    padding: 0.75rem;
    border-radius: 0.25rem;
    overflow: auto;
    margin: 0.5rem 0;
  }

  :global(html:not(.dark) .prose pre) {
    background-color: #f3f4f6;
    color: #1f2937;
  }

  :global(html.dark .prose pre) {
    background-color: #1f2937;
    color: #f3f4f6;
  }

  :global(.prose table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }

  :global(.prose table th),
  :global(.prose table td) {
    padding: 0.75rem;
    text-align: left;
  }

  :global(html:not(.dark) .prose table th),
  :global(html:not(.dark) .prose table td) {
    border: 1px solid #d1d5db;
  }

  :global(html.dark .prose table th),
  :global(html.dark .prose table td) {
    border: 1px solid #4b5563;
  }

  :global(.prose table th) {
    font-weight: 600;
  }

  :global(html:not(.dark) .prose table th) {
    background-color: #f3f4f6;
  }

  :global(html.dark .prose table th) {
    background-color: #374151;
  }

  :global(html:not(.dark) .prose table tr:nth-child(even)) {
    background-color: rgba(0, 0, 0, 0.02);
  }

  :global(html.dark .prose table tr:nth-child(even)) {
    background-color: rgba(255, 255, 255, 0.02);
  }
</style>
