# System7 UI Quick Reference

Quick guide for using System7 classic Mac components in uDOS.

## Import Components

```typescript
import { Window, Button, Checkbox, Alert } from "$lib/components/system7";
```

## Window

Draggable, resizable classic Mac window.

```svelte
<Window
  title="My Window"
  x={100}
  y={100}
  width={400}
  height={300}
  active={true}
  resizable={true}
  closeable={true}
  onClose={() => handleClose()}
>
  <p>Window content goes here</p>
</Window>
```

**Props**:

- `title`: string (default: "Untitled")
- `x`, `y`: number - Window position
- `width`, `height`: number - Window dimensions
- `active`: boolean - Active state (striped title bar)
- `resizable`: boolean - Show resize grip
- `closeable`: boolean - Show close box
- `onClose`: () => void - Close callback

## Button

System 7 style button with 3D effect.

```svelte
<Button
  label="Save"
  variant="default"
  disabled={false}
  onClick={() => handleClick()}
/>
```

**Props**:

- `label`: string - Button text
- `variant`: 'default' | 'cancel' - Button style
- `disabled`: boolean - Disabled state
- `onClick`: () => void - Click handler

**Variants**:

- `default`: Bold 3px border (primary action)
- `cancel`: Normal 1px border (secondary action)

## Checkbox

Classic checkbox with checkmark.

```svelte
<Checkbox
  label="Enable feature"
  checked={false}
  disabled={false}
  onChange={(value) => handleChange(value)}
/>
```

**Props**:

- `label`: string - Checkbox label
- `checked`: boolean - Checked state
- `disabled`: boolean - Disabled state
- `onChange`: (checked: boolean) => void - Change handler

## Alert

Modal alert dialog with icon.

```svelte
<Alert
  type="caution"
  title="Warning"
  message="Are you sure you want to delete this file?"
  buttons={[
    { label: 'Cancel', variant: 'cancel', action: () => {} },
    { label: 'Delete', variant: 'default', action: () => deleteFile() }
  ]}
  onClose={() => closeAlert()}
/>
```

**Props**:

- `type`: 'stop' | 'caution' | 'note' - Alert icon type
- `title`: string - Alert title
- `message`: string - Alert message
- `buttons`: Array<{label, variant?, action}> - Button config
- `onClose`: () => void - Close callback

**Alert Types**:

- `stop`: Red X icon (errors, critical issues)
- `caution`: Yellow triangle (warnings, confirmations)
- `note`: Blue info icon (notifications, tips)

## Colors

```typescript
import { SYSTEM7_COLORS } from "$lib/styles/system7";

SYSTEM7_COLORS.windowChrome; // #dddddd
SYSTEM7_COLORS.titleBarActive; // #000000
SYSTEM7_COLORS.buttonFace; // #dddddd
SYSTEM7_COLORS.highlight; // #ffffff
SYSTEM7_COLORS.shadow; // #888888
```

## Fonts

```typescript
import { SYSTEM7_FONTS } from "$lib/styles/system7";

SYSTEM7_FONTS.system; // 'Chicago'
SYSTEM7_FONTS.app; // 'Geneva'
SYSTEM7_FONTS.mono; // 'Monaco'
SYSTEM7_FONTS.heading; // 'Charcoal'
```

## Icons

System7 sprite paths:

```typescript
// Desktop icons
"/sprites/system7/icons/folder.svg";
"/sprites/system7/icons/document.svg";
"/sprites/system7/icons/trash-empty.svg";

// Alert icons
"/sprites/system7/alerts/stop.svg";
"/sprites/system7/alerts/caution.svg";
"/sprites/system7/alerts/note.svg";

// Controls
"/sprites/system7/controls/checkbox-checked.svg";
"/sprites/system7/controls/radio-selected.svg";
"/sprites/system7/controls/scrollbar-up.svg";
```

## Example: Desktop File Browser

```svelte
<script lang="ts">
  import { Window, Alert } from '$lib/components/system7';

  let showDeleteAlert = false;
  let selectedFile = '';

  function deleteFile() {
    showDeleteAlert = true;
  }

  function confirmDelete() {
    // Delete logic here
    showDeleteAlert = false;
  }
</script>

<Window title="Documents" x={50} y={50} width={500} height={400}>
  <div class="file-list">
    {#each files as file}
      <div class="file-item" on:click={() => selectedFile = file.name}>
        <img src="/sprites/system7/icons/{file.type}.svg" width="32" />
        <span>{file.name}</span>
      </div>
    {/each}
  </div>

  <div class="toolbar">
    <Button label="Open" variant="default" />
    <Button label="Delete" onClick={deleteFile} />
  </div>
</Window>

{#if showDeleteAlert}
  <Alert
    type="caution"
    title="Delete File"
    message="Are you sure you want to delete '{selectedFile}'? This cannot be undone."
    buttons={[
      { label: 'Cancel', variant: 'cancel', action: () => showDeleteAlert = false },
      { label: 'Delete', variant: 'default', action: confirmDelete }
    ]}
    onClose={() => showDeleteAlert = false}
  />
{/if}

<style>
  .file-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 16px;
    padding: 16px;
  }

  .file-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    padding: 8px;
    border: 1px solid transparent;
  }

  .file-item:hover {
    background: #e0e0e0;
    border-color: #999;
  }

  .toolbar {
    display: flex;
    gap: 8px;
    padding: 8px;
    border-top: 1px solid #ccc;
  }
</style>
```

## Desktop Background

Classic teal pattern:

```css
.desktop {
  background: #008080;
  background-image: repeating-linear-gradient(
    45deg,
    #008080 0px,
    #008080 10px,
    #007070 10px,
    #007070 20px
  );
}
```

## Tailwind Mappings

```typescript
import { SYSTEM7_TAILWIND_MAP } from "$lib/styles/system7";

// system.css class → Tailwind equivalent
SYSTEM7_TAILWIND_MAP["window"]; // Tailwind classes for window
SYSTEM7_TAILWIND_MAP["title-bar"]; // Tailwind classes for title bar
SYSTEM7_TAILWIND_MAP["button"]; // Tailwind classes for button
```

## Tips

1. **Z-index**: Windows use z-index 100 (inactive) and 1000 (active)
2. **Dragging**: Only title bar area is draggable
3. **Fonts**: Load Chicago font for authentic System 7 look
4. **Colors**: Stick to grayscale palette with minimal accent colors
5. **Spacing**: Use 8px grid for consistent alignment

## See Also

- [Icon Library README](/static/icons/README.md) - All icon sources
- [System7 Demo](/system7) - Interactive component showcase
- [system.css](https://sakofchit.github.io/system.css/) - Original inspiration

---

Last Updated: 2026-01-11
