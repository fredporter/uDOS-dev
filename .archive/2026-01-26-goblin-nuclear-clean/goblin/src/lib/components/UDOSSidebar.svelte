<script lang="ts">
  /**
   * uDOS Sidebar - Right-hand side utility panel
   * Uses UDOS 32-Color Palette v2.0.0
   * PressStart2P font for retro grid aesthetic
   * Flat block-style buttons (no rounded edges, no borders)
   */
</script>

<div
  class="w-64 overflow-y-auto relative"
  style="z-index: 20; background-color: var(--color-udos-black); font-family: var(--font-family-pressstart);"
>
  <div class="p-3 space-y-3">
    <!-- Keypad Section -->
    <div class="p-2" style="background-color: var(--color-udos-dark-grey);">
      <h3
        class="text-[8px] font-bold mb-2 uppercase tracking-wider"
        style="color: var(--color-udos-cyan);"
      >
        Keypad
      </h3>
      <div class="grid grid-cols-4 gap-0.5">
        <!-- Row 0: Command/Shift / * - -->
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-cyan); color: var(--color-udos-black);"
          title="Command/Shift"
        >
          <span>⌘⇧</span>
        </button>
        <button
          class="px-1 py-2 text-[10px] hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-magenta); color: var(--color-udos-white);"
          >/</button
        >
        <button
          class="px-1 py-2 text-[10px] hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-magenta); color: var(--color-udos-white);"
          >*</button
        >
        <button
          class="px-1 py-2 text-[10px] hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-magenta); color: var(--color-udos-white);"
          >−</button
        >

        <!-- Row 1: 7/Home 8/^ 9/PgUp + -->
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="7 / Home"
        >
          <span style="color: var(--color-udos-cyan);">Home</span>
          <span>7</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="8 / Up Arrow"
        >
          <span style="color: var(--color-udos-cyan);">↑</span>
          <span>8</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="9 / Page Up"
        >
          <span style="color: var(--color-udos-cyan);">PgUp</span>
          <span>9</span>
        </button>
        <button
          class="px-1 py-2 text-[10px] row-span-2 hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-magenta); color: var(--color-udos-white);"
          >+</button
        >

        <!-- Row 2: 4/< 5/OK 6/> (+ continues) -->
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="4 / Left Arrow"
        >
          <span style="color: var(--color-udos-cyan);">←</span>
          <span>4</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="5 / OK"
        >
          <span style="color: var(--color-udos-cyan);">OK</span>
          <span>5</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="6 / Right Arrow"
        >
          <span style="color: var(--color-udos-cyan);">→</span>
          <span>6</span>
        </button>

        <!-- Row 3: 1/End 2/v 3/PgDn Enter/= -->
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="1 / End"
        >
          <span style="color: var(--color-udos-cyan);">End</span>
          <span>1</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="2 / Down Arrow"
        >
          <span style="color: var(--color-udos-cyan);">↓</span>
          <span>2</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="3 / Page Down"
        >
          <span style="color: var(--color-udos-cyan);">PgDn</span>
          <span>3</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] row-span-2 flex items-center justify-center hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-cyan); color: var(--color-udos-black);"
          title="Enter / Equals">⏎</button
        >

        <!-- Row 4: 0/Redo ./Undo (Enter continues) -->
        <button
          class="px-1 py-2 text-[8px] col-span-2 flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title="0 / Redo"
        >
          <span style="color: var(--color-udos-cyan);">Redo</span>
          <span>0</span>
        </button>
        <button
          class="px-1 py-2 text-[8px] flex flex-col items-center leading-tight hover:brightness-125 transition-none active:translate-y-0.5"
          style="background-color: var(--color-udos-charcoal); color: var(--color-udos-off-white);"
          title=". / Undo"
        >
          <span style="color: var(--color-udos-cyan);">Undo</span>
          <span>.</span>
        </button>
      </div>
    </div>

    <!-- F-Keys Section -->
    <div class="p-2" style="background-color: var(--color-udos-dark-grey);">
      <h3
        class="text-[8px] font-bold mb-2 uppercase tracking-wider"
        style="color: var(--color-udos-safe);"
      >
        F-Keys
      </h3>
      <div class="grid grid-cols-4 gap-0.5">
        {#each Array(12) as _, i}
          <button
            class="px-1 py-1.5 text-[8px] hover:brightness-125 transition-none active:translate-y-0.5"
            style="background-color: var(--color-udos-{i < 4
              ? 'danger'
              : i < 8
                ? 'waypoint'
                : 'safe'}); color: var(--color-udos-{i < 4 || i >= 8
              ? 'white'
              : 'black'});">F{i + 1}</button
          >
        {/each}
      </div>
    </div>

    <!-- Quick Keys Section -->
    <div class="p-2" style="background-color: var(--color-udos-dark-grey);">
      <h3
        class="text-[8px] font-bold mb-2 uppercase tracking-wider"
        style="color: var(--color-udos-waypoint);"
      >
        Quick Keys
      </h3>
      <div
        class="space-y-0.5 text-[8px]"
        style="color: var(--color-udos-off-white);"
      >
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘N</span>
          <span>New</span>
        </div>
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘O</span>
          <span>Open</span>
        </div>
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘S</span>
          <span>Save</span>
        </div>
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘P</span>
          <span>Print</span>
        </div>
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘Z</span>
          <span>Undo</span>
        </div>
        <div
          class="flex justify-between px-2 py-1 hover:brightness-125"
          style="background-color: var(--color-udos-charcoal);"
        >
          <span style="color: var(--color-udos-cyan);">⌘⇧Z</span>
          <span>Redo</span>
        </div>
      </div>
    </div>

    <!-- Color Palette Preview -->
    <div class="p-2" style="background-color: var(--color-udos-dark-grey);">
      <h3
        class="text-[8px] font-bold mb-2 uppercase tracking-wider"
        style="color: var(--color-udos-purple);"
      >
        Palette
      </h3>
      <div class="grid grid-cols-8 gap-0">
        <!-- Terrain -->
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-forest);"
          title="Forest"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-grass);"
          title="Grass"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-deep-water);"
          title="Deep Water"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-water);"
          title="Water"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-earth);"
          title="Earth"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-sand);"
          title="Sand"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-mountain);"
          title="Mountain"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-snow);"
          title="Snow"
        ></div>
        <!-- Markers -->
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-danger);"
          title="Danger"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-alert);"
          title="Alert"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-waypoint);"
          title="Waypoint"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-safe);"
          title="Safe"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-cyan);"
          title="Cyan"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-purple);"
          title="Purple"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-pink);"
          title="Pink"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-magenta);"
          title="Magenta"
        ></div>
        <!-- Greyscale -->
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-black);"
          title="Black"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-dark-grey);"
          title="Dark Grey"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-charcoal);"
          title="Charcoal"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-grey);"
          title="Grey"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-steel);"
          title="Steel"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-light-grey);"
          title="Light Grey"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-off-white);"
          title="Off White"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-white);"
          title="White"
        ></div>
        <!-- Accents -->
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-skin-light);"
          title="Skin Light"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-skin-medium);"
          title="Skin Medium"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-skin-tan);"
          title="Skin Tan"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-skin-dark);"
          title="Skin Dark"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-lava);"
          title="Lava"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-ice);"
          title="Ice"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-toxic);"
          title="Toxic"
        ></div>
        <div
          class="w-full aspect-square"
          style="background-color: var(--color-udos-deep-sea);"
          title="Deep Sea"
        ></div>
      </div>
    </div>
  </div>
</div>
