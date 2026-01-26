<script lang="ts">
  import Window from "$lib/components/system7/Window.svelte";
  import Button from "$lib/components/system7/Button.svelte";
  import Checkbox from "$lib/components/system7/Checkbox.svelte";
  import Alert from "$lib/components/system7/Alert.svelte";

  let showWindow1 = true;
  let showWindow2 = true;
  let showAlert = false;
  let checkboxValue = false;

  function openAlert() {
    showAlert = true;
  }

  function closeAlert() {
    showAlert = false;
  }
</script>

<svelte:head>
  <title>System 7 UI Demo - Markdown</title>
</svelte:head>

<div class="desktop">
  <h1>System 7 UI Components</h1>
  <p class="intro">
    Classic Mac System 7 style UI elements, inspired by <a
      href="https://sakofchit.github.io/system.css/"
      target="_blank">system.css</a
    >
  </p>

  <div class="controls">
    <Button label="Open Alert" variant="default" onClick={openAlert} />
    <Button label="Show Window 1" onClick={() => (showWindow1 = true)} />
    <Button label="Show Window 2" onClick={() => (showWindow2 = true)} />
  </div>

  <div class="sprites-gallery">
    <h2>System 7 Sprites</h2>

    <section>
      <h3>Icons</h3>
      <div class="sprite-row">
        <div class="sprite-item">
          <img
            src="/sprites/system7/icons/folder.svg"
            alt="Folder"
            width="32"
          />
          <span>Folder</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/icons/document.svg"
            alt="Document"
            width="32"
          />
          <span>Document</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/icons/trash-empty.svg"
            alt="Trash"
            width="32"
          />
          <span>Trash</span>
        </div>
      </div>
    </section>

    <section>
      <h3>Buttons & Controls</h3>
      <div class="sprite-row">
        <div class="sprite-item">
          <img
            src="/sprites/system7/buttons/button-default.svg"
            alt="Default Button"
            width="80"
          />
          <span>Default Button</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/controls/checkbox-checked.svg"
            alt="Checkbox"
            width="14"
          />
          <span>Checkbox</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/controls/radio-selected.svg"
            alt="Radio"
            width="14"
          />
          <span>Radio Button</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/controls/scrollbar-up.svg"
            alt="Scrollbar"
            width="16"
          />
          <span>Scrollbar</span>
        </div>
      </div>
    </section>

    <section>
      <h3>Alert Icons</h3>
      <div class="sprite-row">
        <div class="sprite-item">
          <img src="/sprites/system7/alerts/stop.svg" alt="Stop" width="32" />
          <span>Stop</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/alerts/caution.svg"
            alt="Caution"
            width="32"
          />
          <span>Caution</span>
        </div>
      </div>
    </section>

    <section>
      <h3>Window Chrome</h3>
      <div class="sprite-row">
        <div class="sprite-item">
          <img
            src="/sprites/system7/windows/titlebar-active.svg"
            alt="Title Bar"
            width="200"
          />
          <span>Title Bar</span>
        </div>
        <div class="sprite-item">
          <img
            src="/sprites/system7/windows/resize-box.svg"
            alt="Resize Box"
            width="16"
          />
          <span>Resize Box</span>
        </div>
      </div>
    </section>
  </div>

  <div class="component-examples">
    <h2>Interactive Components</h2>

    <section>
      <h3>Buttons</h3>
      <div class="button-row">
        <Button label="Default" variant="default" />
        <Button label="Cancel" variant="cancel" />
        <Button label="Disabled" disabled={true} />
      </div>
    </section>

    <section>
      <h3>Checkboxes</h3>
      <Checkbox label="Option 1" checked={true} />
      <Checkbox label="Option 2" checked={false} />
      <Checkbox label="Disabled" checked={false} disabled={true} />
    </section>
  </div>
</div>

{#if showWindow1}
  <Window
    title="Example Window"
    x={150}
    y={100}
    width={400}
    height={300}
    onClose={() => (showWindow1 = false)}
  >
    <h2>Classic Mac Window</h2>
    <p>This is a draggable System 7 style window with:</p>
    <ul>
      <li>Striped title bar</li>
      <li>Close box (top-left)</li>
      <li>Resize grip (bottom-right)</li>
      <li>Drop shadow</li>
    </ul>

    <div style="margin-top: 16px;">
      <Button
        label="Click Me"
        variant="default"
        onClick={() => alert("Button clicked!")}
      />
    </div>
  </Window>
{/if}

{#if showWindow2}
  <Window
    title="Settings"
    x={250}
    y={150}
    width={320}
    height={240}
    onClose={() => (showWindow2 = false)}
  >
    <h3>Preferences</h3>

    <div style="margin: 16px 0;">
      <Checkbox
        label="Enable Classic Mode"
        checked={checkboxValue}
        onChange={(val: boolean) => (checkboxValue = val)}
      />
      <Checkbox label="Show Desktop Icons" checked={true} />
      <Checkbox label="Startup Sound" checked={false} />
    </div>

    <div style="margin-top: 24px; text-align: right;">
      <Button
        label="Cancel"
        variant="cancel"
        onClick={() => (showWindow2 = false)}
      />
      <Button
        label="Save"
        variant="default"
        onClick={() => (showWindow2 = false)}
      />
    </div>
  </Window>
{/if}

{#if showAlert}
  <Alert
    type="caution"
    title="System 7 Alert"
    message="This is a classic Mac alert dialog. Are you sure you want to proceed?"
    buttons={[
      { label: "Cancel", variant: "cancel", action: closeAlert },
      { label: "OK", variant: "default", action: closeAlert },
    ]}
    onClose={closeAlert}
  />
{/if}

<style>
  .desktop {
    min-height: 100vh;
    background: #008080; /* Classic Mac desktop teal */
    background-image: repeating-linear-gradient(
      45deg,
      #008080 0px,
      #008080 10px,
      #007070 10px,
      #007070 20px
    );
    padding: 20px;
    font-family: "Geneva", "Helvetica Neue", sans-serif;
  }

  h1 {
    font-family: "Chicago", "Press Start 2P", monospace;
    font-size: 24px;
    color: #ffffff;
    text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.5);
    margin-bottom: 8px;
  }

  .intro {
    color: #ffffff;
    font-size: 14px;
    margin-bottom: 24px;
  }

  .intro a {
    color: #ffff00;
    text-decoration: underline;
  }

  .controls {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
  }

  .sprites-gallery,
  .component-examples {
    background: #ffffff;
    border: 2px solid #000000;
    padding: 16px;
    margin-bottom: 24px;
    box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.3);
  }

  h2 {
    font-family: "Chicago", "Press Start 2P", monospace;
    font-size: 16px;
    margin: 0 0 16px 0;
  }

  h3 {
    font-family: "Geneva", "Helvetica Neue", sans-serif;
    font-size: 14px;
    font-weight: bold;
    margin: 16px 0 8px 0;
  }

  section {
    margin-bottom: 16px;
  }

  .sprite-row {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
  }

  .sprite-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .sprite-item span {
    font-size: 11px;
    color: #666;
  }

  .sprite-item img {
    border: 1px solid #ccc;
    background: repeating-conic-gradient(#eeeeee 0% 25%, #ffffff 0% 50%) 50% /
      10px 10px;
  }

  .button-row {
    display: flex;
    gap: 8px;
  }

  ul {
    font-size: 12px;
    line-height: 1.6;
  }
</style>
