<script lang="ts">
  // Input sidebar - synthwave-styled keypad (not affected by light/dark mode)
  import { emit } from "@tauri-apps/api/event";

  // F-key labels and actions
  const fKeys = [
    { num: 1, label: "Help", key: "F1", alias: "⌘1" },
    { num: 2, label: "Edit", key: "F2", alias: "⌘2" },
    { num: 3, label: "Files", key: "F3", alias: "⌘3" },
    { num: 4, label: "Mode+", key: "F4", alias: "⌘4" },
    { num: 5, label: "Reload", key: "F5", alias: "⌘5" },
    { num: 6, label: "Buffer", key: "F6", alias: "⌘6" },
    { num: 7, label: "Mode−", key: "F7", alias: "⌘7" },
    { num: 8, label: "Present", key: "F8", alias: "⌘8" },
    { num: 9, label: "Term", key: "F9", alias: "⌘9" },
    { num: 10, label: "Restart", key: "F10", alias: "⌘0" },
    { num: 11, label: "Full", key: "F11", alias: "⌘−" },
    { num: 12, label: "Dev", key: "F12", alias: "⌘=" },
  ];

  async function triggerFKey(key: string) {
    console.log(`[InputSidebar] Triggering ${key}`);
    const event = new KeyboardEvent("keydown", {
      key: key,
      metaKey: true,
      bubbles: true,
      cancelable: true,
    });
    document.dispatchEvent(event);
  }
</script>

<div
  class="w-72 border-l border-gray-700 overflow-y-auto relative"
  style="z-index: 20; background: linear-gradient(180deg, #1a0b2e 0%, #2d1b4e 100%); font-size: 18px;"
>
  <div class="p-4 space-y-4">
    <!-- Keypad Section -->
    <div
      class="rounded-lg p-3"
      style="background: rgba(255, 71, 255, 0.1); border: 1px solid rgba(255, 71, 255, 0.3);"
    >
      <h3 class="text-base font-bold mb-3" style="color: #ff47ff;">
        Keypad & Calculator
      </h3>
      <div class="grid grid-cols-4 gap-2">
        <!-- Row 0: Command/Shift / * - -->
        <button
          class="px-3 py-3 rounded text-base font-mono flex flex-col items-center leading-tight hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #00f5ff 0%, #00ccff 100%); color: #000; box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);"
          title="Command/Shift"
        >
          <span class="text-sm">⌘⇧</span>
        </button>
        <button
          class="px-4 py-3 rounded text-xl font-mono hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #ff47ff 0%, #ff007a 100%); color: #fff; box-shadow: 0 4px 15px rgba(255, 71, 255, 0.3);"
          >/</button
        >
        <button
          class="px-4 py-3 rounded text-xl font-mono hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #ff47ff 0%, #ff007a 100%); color: #fff; box-shadow: 0 4px 15px rgba(255, 71, 255, 0.3);"
          >*</button
        >
        <button
          class="px-4 py-3 rounded text-xl font-mono hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #ff47ff 0%, #ff007a 100%); color: #fff; box-shadow: 0 4px 15px rgba(255, 71, 255, 0.3);"
          >−</button
        >

        <!-- Row 1: 7/Home 8/^ 9/PgUp + -->
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="7 / Home"
        >
          <span class="text-xs" style="color: #00f5ff;">Home</span>
          <span>7</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="8 / Up Arrow"
        >
          <span class="text-xs" style="color: #00f5ff;">↑</span>
          <span>8</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="9 / Page Up"
        >
          <span class="text-xs" style="color: #00f5ff;">PgUp</span>
          <span>9</span>
        </button>
        <button
          class="px-4 py-3 rounded text-xl font-mono row-span-2 hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #ff47ff 0%, #ff007a 100%); color: #fff; box-shadow: 0 4px 15px rgba(255, 71, 255, 0.3);"
          >+</button
        >

        <!-- Row 2: 4/< 5/OK 6/> (+ continues) -->
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="4 / Left Arrow"
        >
          <span class="text-xs" style="color: #00f5ff;">←</span>
          <span>4</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="5 / OK"
        >
          <span class="text-xs" style="color: #00f5ff;">OK</span>
          <span>5</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="6 / Right Arrow"
        >
          <span class="text-xs" style="color: #00f5ff;">→</span>
          <span>6</span>
        </button>

        <!-- Row 3: 1/End 2/v 3/PgDn Enter/= -->
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="1 / End"
        >
          <span class="text-xs" style="color: #00f5ff;">End</span>
          <span>1</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="2 / Down Arrow"
        >
          <span class="text-xs" style="color: #00f5ff;">↓</span>
          <span>2</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="3 / Page Down"
        >
          <span class="text-xs" style="color: #00f5ff;">PgDn</span>
          <span>3</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono row-span-2 flex items-center justify-center hover:brightness-110 transition"
          style="background: linear-gradient(135deg, #00f5ff 0%, #00ccff 100%); color: #000; box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);"
          title="Enter / Equals">⏎<br />=</button
        >

        <!-- Row 4: 0/Redo ./Undo (Enter continues) -->
        <button
          class="px-3 py-3 rounded text-lg font-mono col-span-2 flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title="0 / Redo"
        >
          <span class="text-xs" style="color: #00f5ff;">Redo</span>
          <span>0</span>
        </button>
        <button
          class="px-3 py-3 rounded text-lg font-mono flex flex-col items-center leading-tight hover:bg-opacity-90 transition"
          style="background: rgba(138, 43, 226, 0.2); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
          title=". / Undo"
        >
          <span class="text-xs" style="color: #00f5ff;">Undo</span>
          <span>.</span>
        </button>
      </div>
    </div>

    <!-- F-Keys Section -->
    <div
      class="rounded-lg p-4"
      style="background: rgba(0, 245, 255, 0.1); border: 1px solid rgba(0, 245, 255, 0.3);"
    >
      <h3 class="text-base font-bold mb-3" style="color: #00f5ff;">
        Function Keys
      </h3>
      <div class="grid grid-cols-2 gap-2">
        {#each fKeys as fk}
          <button
            class="px-2 py-2 rounded text-sm font-mono hover:brightness-125 transition flex flex-col items-center leading-tight"
            style="background: rgba(138, 43, 226, 0.3); color: #e0e0e0; border: 1px solid rgba(138, 43, 226, 0.5);"
            onclick={() => triggerFKey(fk.key)}
            title="{fk.key} / {fk.alias}"
          >
            <span class="text-xs" style="color: #00f5ff;">{fk.label}</span>
            <span class="text-xs opacity-70">{fk.key}</span>
          </button>
        {/each}
      </div>
    </div>

    <!-- Keyboard Layout Section -->
    <div
      class="rounded-lg p-4"
      style="background: rgba(255, 71, 255, 0.1); border: 1px solid rgba(255, 71, 255, 0.3);"
    >
      <h3 class="text-base font-bold mb-3" style="color: #ff47ff;">
        Quick Keys
      </h3>
      <div class="space-y-2 text-sm font-mono" style="color: #e0e0e0;">
        <div class="flex justify-between">
          <span style="color: #00f5ff;">⌘K</span>
          <span>Flyin</span>
        </div>
        <div class="flex justify-between">
          <span style="color: #00f5ff;">⌘T</span>
          <span>Ticker</span>
        </div>
        <div class="flex justify-between">
          <span style="color: #00f5ff;">⌘B</span>
          <span>Sidebar</span>
        </div>
        <div class="flex justify-between">
          <span style="color: #00f5ff;">⌘P</span>
          <span>Keypad</span>
        </div>
        <div class="flex justify-between">
          <span style="color: #00f5ff;">Select</span>
          <span>Auto-Copy</span>
        </div>
      </div>
    </div>
  </div>
</div>
