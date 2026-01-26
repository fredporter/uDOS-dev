<script lang="ts">
  export let label = "";
  export let checked = false;
  export let disabled = false;
  export let onChange: ((checked: boolean) => void) | undefined = undefined;

  function handleChange() {
    if (disabled) return;
    checked = !checked;
    if (onChange) onChange(checked);
  }
</script>

<label class="system7-checkbox" class:disabled>
  <button
    type="button"
    role="checkbox"
    class="checkbox-box"
    class:checked
    aria-checked={checked}
    aria-label={label}
    on:click={handleChange}
  >
    {#if checked}
      <svg viewBox="0 0 14 14" class="checkmark">
        <path
          d="M 3 7 L 6 10 L 11 4"
          stroke="#000000"
          stroke-width="2"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    {/if}
  </button>
  <span class="checkbox-label">{label}</span>
</label>

<style>
  .system7-checkbox {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    user-select: none;
    font-family: "Geneva", "Helvetica Neue", sans-serif;
    font-size: 12px;
  }

  .system7-checkbox.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .checkbox-box {
    width: 14px;
    height: 14px;
    padding: 0;
    background: #ffffff;
    border: 2px solid #000000;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    cursor: pointer;
  }

  .checkbox-box:hover:not(.disabled) {
    background: #f0f0f0;
  }

  .checkmark {
    width: 12px;
    height: 12px;
  }

  .checkbox-label {
    color: #000000;
  }

  .disabled .checkbox-label {
    color: #888888;
  }
</style>
