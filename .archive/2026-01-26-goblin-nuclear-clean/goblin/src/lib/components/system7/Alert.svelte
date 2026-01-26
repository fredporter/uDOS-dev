<script lang="ts">
  export let type: "stop" | "caution" | "note" = "note";
  export let title = "";
  export let message = "";
  export let buttons: {
    label: string;
    action: () => void;
    variant?: "default" | "cancel";
  }[] = [{ label: "OK", action: () => {}, variant: "default" }];
  export let onClose: (() => void) | undefined = undefined;

  import Button from "./Button.svelte";

  const icons = {
    stop: "/sprites/system7/alerts/stop.svg",
    caution: "/sprites/system7/alerts/caution.svg",
    note: "/sprites/system7/alerts/note.svg",
  };

  function handleButtonClick(button: (typeof buttons)[0]) {
    button.action();
    if (onClose) onClose();
  }
</script>

<div class="system7-alert-overlay">
  <div class="system7-alert">
    <!-- Title Bar -->
    <div class="alert-title-bar">
      <span class="alert-title">{title || "Alert"}</span>
    </div>

    <!-- Alert Content -->
    <div class="alert-content">
      <!-- Icon -->
      <div class="alert-icon">
        <img src={icons[type]} alt="{type} icon" />
      </div>

      <!-- Message -->
      <div class="alert-message">
        <p>{message}</p>
      </div>
    </div>

    <!-- Buttons -->
    <div class="alert-buttons">
      {#each buttons as button}
        <Button
          label={button.label}
          variant={button.variant || "default"}
          onClick={() => handleButtonClick(button)}
        />
      {/each}
    </div>
  </div>
</div>

<style>
  .system7-alert-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  }

  .system7-alert {
    width: 320px;
    background: #ffffff;
    border: 2px solid #000000;
    box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.5);
  }

  .alert-title-bar {
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
    justify-content: center;
  }

  .alert-title {
    font-family: "Chicago", "Press Start 2P", monospace;
    font-size: 12px;
    color: #ffffff;
    font-weight: bold;
    text-shadow: 1px 1px 0 rgba(0, 0, 0, 0.5);
  }

  .alert-content {
    display: flex;
    gap: 16px;
    padding: 16px;
    min-height: 80px;
  }

  .alert-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
  }

  .alert-icon img {
    width: 100%;
    height: 100%;
  }

  .alert-message {
    flex: 1;
    font-family: "Geneva", "Helvetica Neue", sans-serif;
    font-size: 12px;
    line-height: 1.4;
    color: #000000;
  }

  .alert-message p {
    margin: 0;
  }

  .alert-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 0 16px 16px 16px;
  }
</style>
