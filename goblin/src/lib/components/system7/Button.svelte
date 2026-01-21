<script lang="ts">
  export let label = "";
  export let variant: "default" | "cancel" = "default";
  export let disabled = false;
  export let onClick: (() => void) | undefined = undefined;

  function handleClick() {
    if (disabled) return;
    if (onClick) onClick();
  }
</script>

<button
  class="system7-button"
  class:default={variant === "default"}
  class:cancel={variant === "cancel"}
  class:disabled
  on:click={handleClick}
  {disabled}
>
  <span class="button-label">{label}</span>
</button>

<style>
  .system7-button {
    position: relative;
    min-width: 80px;
    height: 20px;
    padding: 0 12px;
    background: #dddddd;
    border: 1px solid #000000;
    border-radius: 2px;
    font-family: "Chicago", "Press Start 2P", monospace;
    font-size: 10px;
    color: #000000;
    cursor: pointer;
    user-select: none;
    text-align: center;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  /* Default button has bold border */
  .system7-button.default {
    border-width: 3px;
    padding: 0 10px;
  }

  /* 3D effect */
  .system7-button::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-top: 1px solid #ffffff;
    border-left: 1px solid #ffffff;
    border-bottom: 1px solid #888888;
    border-right: 1px solid #888888;
    pointer-events: none;
  }

  .system7-button:hover:not(:disabled) {
    background: #eeeeee;
  }

  .system7-button:active:not(:disabled) {
    background: #cccccc;
    transform: translateY(1px);
  }

  .system7-button:disabled,
  .system7-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .button-label {
    position: relative;
    z-index: 1;
  }
</style>
