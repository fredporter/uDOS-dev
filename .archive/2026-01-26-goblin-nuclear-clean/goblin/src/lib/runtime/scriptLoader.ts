/**
 * uDOS Script Loader
 *
 * Loads and parses udos.md scripts with uPY configuration
 */

export interface UdosScript {
  content: string;
  config: any;
  messages: string[];
}

/**
 * Load a udos.md script from the scripts directory
 */
export async function loadScript(
  scriptName: string
): Promise<UdosScript | null> {
  try {
    console.log(`[scriptLoader] Loading script: ${scriptName}`);
    const response = await fetch(`/scripts/${scriptName}.udos.md`);
    console.log(`[scriptLoader] Fetch response status: ${response.status}`);
    if (!response.ok) {
      console.error(
        `[scriptLoader] Failed to fetch script: ${response.status} ${response.statusText}`
      );
      return null;
    }

    const content = await response.text();
    console.log(`[scriptLoader] Script content length: ${content.length}`);
    const parsed = parseScript(content);
    console.log(`[scriptLoader] Parsed ${parsed.messages.length} messages`);
    return parsed;
  } catch (error) {
    console.error(`[scriptLoader] Error loading script ${scriptName}:`, error);
    return null;
  }
}

/**
 * Parse a udos.md script and extract uPY configuration
 */
export function parseScript(content: string): UdosScript {
  const lines = content.split("\n");
  const messages: string[] = [];
  let config: any = {};
  let inCodeBlock = false;
  let codeBlockContent = "";
  let isUpyBlock = false;

  for (const line of lines) {
    // Detect code block start
    if (line.trim().startsWith("```upy")) {
      inCodeBlock = true;
      isUpyBlock = true;
      codeBlockContent = "";
      continue;
    }

    // Detect code block end
    if (inCodeBlock && line.trim() === "```") {
      inCodeBlock = false;
      if (isUpyBlock) {
        // Parse YAML-like config and merge with existing
        const newConfig = parseUpyConfig(codeBlockContent);
        config = { ...config, ...newConfig };
        isUpyBlock = false;
      }
      continue;
    }

    // Collect code block content
    if (inCodeBlock) {
      codeBlockContent += line + "\n";
      continue;
    }
  }

  // Extract messages from various config structures
  // 1. Check for bootSequence.messages (startup scripts)
  console.log("[scriptLoader] Checking bootSequence:", config.bootSequence);
  if (config.bootSequence?.messages) {
    console.log(
      "[scriptLoader] bootSequence.messages:",
      config.bootSequence.messages
    );
    console.log(
      "[scriptLoader] Is array?",
      Array.isArray(config.bootSequence.messages)
    );
    for (const msg of config.bootSequence.messages) {
      if (msg.text !== undefined) {
        messages.push(msg.text);
      }
    }
  }

  // 2. Check for stages with messages (reboot scripts)
  console.log("[scriptLoader] Checking stages:", config.stages);
  if (config.stages && Array.isArray(config.stages)) {
    for (const stage of config.stages) {
      if (stage.messages && Array.isArray(stage.messages)) {
        for (const msg of stage.messages) {
          messages.push(msg);
        }
      }
    }
  }

  // Debug logging
  console.log("[scriptLoader] Parsed config:", config);
  console.log("[scriptLoader] Extracted messages:", messages);

  return { content, config, messages };
}

/**
 * Parse uPY YAML-like configuration
 */
function parseUpyConfig(content: string): any {
  const config: any = {};
  const lines = content.split("\n");
  const stack: Array<{ obj: any; indent: number; key?: string }> = [
    { obj: config, indent: -1 },
  ];

  console.log("[scriptLoader] Starting YAML parse, lines:", lines.length);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip comments and empty lines
    if (!trimmed || trimmed.startsWith("#")) continue;

    const indent = line.length - line.trimLeft().length;

    // Pop stack to correct indentation level
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const current = stack[stack.length - 1];

    console.log(
      `[scriptLoader] Line ${i}: indent=${indent}, current.key=${current.key}, line="${trimmed.substring(0, 50)}"`
    );

    // Array item (starts with -)
    if (trimmed.startsWith("-")) {
      const content = trimmed.slice(1).trim();

      const current = stack[stack.length - 1];

      // Must have parent key context
      if (!current.key) {
        console.warn("[scriptLoader] Array item without parent key");
        continue;
      }

      // Get the parent object and ensure the key is an array
      const parentObj = current.obj[current.key];
      if (!Array.isArray(parentObj)) {
        // Convert object placeholder to array
        current.obj[current.key] = [];
      }
      const targetArray = current.obj[current.key];

      if (content.includes(":")) {
        // Object item with key-value pair
        const obj: any = {};
        targetArray.push(obj);
        // Push this object as the new context for nested properties
        stack.push({ obj, indent, key: undefined });
        // Parse the first key-value on same line
        const [key, ...valueParts] = content.split(":");
        const value = valueParts.join(":").trim();
        if (value) {
          obj[key.trim()] = parseValue(value);
        } else {
          // Key with no value - will be populated by nested content
          obj[key.trim()] = {};
        }
      } else {
        // Simple value
        targetArray.push(parseValue(content));
      }
      continue;
    }

    // Key-value pair
    const colonIndex = trimmed.indexOf(":");
    if (colonIndex > 0) {
      const key = trimmed.slice(0, colonIndex).trim();
      const value = trimmed.slice(colonIndex + 1).trim();

      const current = stack[stack.length - 1];

      if (!value || value === "") {
        // Section/object header - will be populated with nested content
        // This could become an array or an object depending on what follows
        // Determine the parent object to add the new property to
        const parentObj = current.key ? current.obj[current.key] : current.obj;

        // Create new empty object for this section
        const newObj = {};
        parentObj[key] = newObj;

        // Push the NEW object to stack so nested content goes into it
        // Include the key for array detection
        stack.push({ obj: parentObj, indent, key });
      } else {
        // Direct value
        const parentObj = current.key ? current.obj[current.key] : current.obj;
        parentObj[key] = parseValue(value);
      }
    }
  }

  return config;
}

/**
 * Parse configuration values (strings, numbers, booleans)
 */
function parseValue(value: string): any {
  const trimmed = value.trim();

  // Boolean
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;

  // Number
  if (/^\d+$/.test(trimmed)) return parseInt(trimmed, 10);
  if (/^\d+\.\d+$/.test(trimmed)) return parseFloat(trimmed);

  // String (remove quotes)
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed.slice(1, -1);
  }

  return trimmed;
}
