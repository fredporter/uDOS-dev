<script lang="ts">
  import { onMount } from "svelte";

  export let title = "Untitled";
  export let width = 400;
  export let height = 300;
  export let x = 100;
  export let y = 100;
  export let active = true;
  export let resizable = true;
  export let closeable = true;
  export let onClose: (() => void) | undefined = undefined;

  let dragging = false;
  let dragOffsetX = 0;
  let dragOffsetY = 0;
  let windowElement: HTMLDivElement;

  function startDrag(e: MouseEvent) {
    if (!(e.target as HTMLElement).closest(".title-bar")) return;
    dragging = true;
    dragOffsetX = e.clientX - x;
    dragOffsetY = e.clientY - y;
  }

  function handleDrag(e: MouseEvent) {
    if (!dragging) return;
    x = e.clientX - dragOffsetX;
    y = e.clientY - dragOffsetY;
  }

  function stopDrag() {
    dragging = false;
  }

  function handleClose() {
    if (onClose) onClose();
  }

  onMount(() => {
    document.addEventListener("mousemove", handleDrag);
    document.addEventListener("mouseup", stopDrag);

    return () => {
      document.removeEventListener("mousemove", handleDrag);
      document.removeEventListener("mouseup", stopDrag);
    };
  });
</script>

<div
  bind:this={windowElement}
  class="system7-window"
  class:active
  style="left: {x}px; top: {y}px; width: {width}px; height: {height}px;"
>
  <!-- Title Bar -->
  <div
    class="title-bar"
    on:mousedown={startDrag}
    role="toolbar"
    tabindex="0"
    on:keydown={(e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
      }
    }}
    aria-label="Window title bar - drag to move"
  >
    <div class="title-bar-stripes" class:active>
      {#if closeable}
        <button
          class="close-box"
          on:click={handleClose}
          aria-label="Close window"
        >
          <div class="close-box-inner"></div>
        </button>
      {/if}
      <span class="title">{title}</span>
    </div>
  </div>

  <!-- Content Area -->
  <div class="window-content">
    <slot />
  </div>

  <!-- Resize Box (bottom-right corner) -->
  {#if resizable}
    <div class="resize-box"></div>
  {/if}
</div>

<style>
  .system7-window {
    position: absolute;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 2px solid #000000;
    box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.3);
    z-index: 100;
  }

  .system7-window.active {
    z-index: 1000;
  }

  /* Title Bar */
  .title-bar {
    cursor: move;
    user-select: none;
    outline: none;
  }

  .title-bar:focus {
    outline: 2px solid #0066cc;
    outline-offset: -2px;
  }

  .title-bar-stripes {
    height: 20px;
    background: #000000;
    background-image: repeating-linear-gradient(
      0deg,
      #000000 0px,
      #000000 2px,
      #ffffff 2px,
      #ffffff 3px
    );
    display: flex;
    align-items: center;
    padding: 0 4px;
    position: relative;
  }

  .title-bar-stripes:not(.active) {
    background: #cccccc;
    background-image: repeating-linear-gradient(
      0deg,
      #cccccc 0px,
      #cccccc 2px,
      #ffffff 2px,
      #ffffff 3px
    );
  }

  .close-box {
    width: 12px;
    height: 12px;
    background: #ffffff;
    border: 1px solid #000000;
    padding: 0;
    margin-right: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-box:hover {
    background: #dddddd;
  }

  .close-box-inner {
    width: 8px;
    height: 8px;
    background: #000000;
  }

  .title {
    flex: 1;
    text-align: center;
    font-family: "Chicago", "Press Start 2P", monospace;
    font-size: 12px;
    color: #ffffff;
    font-weight: bold;
    text-shadow: 1px 1px 0 rgba(0, 0, 0, 0.5);
  }

  .title-bar-stripes:not(.active) .title {
    color: #666666;
  }

  /* Content Area */
  .window-content {
    flex: 1;
    overflow: auto;
    background: #ffffff;
    padding: 8px;
  }

  /* Resize Box */
  .resize-box {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 16px;
    height: 16px;
    background: #dddddd;
    border-left: 1px solid #888888;
    border-top: 1px solid #888888;
    cursor: nwse-resize;
    background-image:
      linear-gradient(135deg, #888888 25%, transparent 25%),
      linear-gradient(225deg, #888888 25%, transparent 25%),
      linear-gradient(45deg, #ffffff 25%, transparent 25%),
      linear-gradient(315deg, #ffffff 25%, transparent 25%);
    background-size: 4px 4px;
    background-position:
      0 0,
      2px 0,
      2px -2px,
      0 -2px;
  }
</style>
