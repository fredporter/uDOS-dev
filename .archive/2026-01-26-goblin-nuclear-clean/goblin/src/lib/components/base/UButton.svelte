<!--
  UButton - Standardized button component for uDOS
  Follows Flowbite patterns with dark mode support and consistent styling
-->
<script lang="ts">
  import type { Snippet } from "svelte";

  type ButtonVariant =
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "danger"
    | "light"
    | "dark"
    | "outline";

  type ButtonSize = "xs" | "sm" | "base" | "lg" | "xl";

  interface Props {
    variant?: ButtonVariant;
    size?: ButtonSize;
    disabled?: boolean;
    loading?: boolean;
    fullWidth?: boolean;
    class?: string;
    onclick?: () => void;
    children?: Snippet;
  }

  let {
    variant = "primary",
    size = "base",
    disabled = false,
    loading = false,
    fullWidth = false,
    class: customClass = "",
    onclick,
    children,
  }: Props = $props();

  const baseClasses = $derived([
    "inline-flex items-center justify-center",
    "font-medium rounded-lg transition-colors duration-200",
    "focus:ring-4 focus:outline-none",
    "active:scale-95 transform",
    disabled || loading
      ? "cursor-not-allowed opacity-50"
      : "cursor-pointer hover:scale-105",
  ]);

  const sizeClasses = {
    xs: "px-3 py-2 text-xs",
    sm: "px-3 py-2 text-sm",
    base: "px-5 py-2.5 text-sm",
    lg: "px-5 py-3 text-base",
    xl: "px-6 py-3.5 text-base",
  };

  const variantClasses = {
    primary: [
      "text-white bg-blue-700 dark:bg-blue-600",
      "hover:bg-blue-800 dark:hover:bg-blue-700",
      "focus:ring-blue-300 dark:focus:ring-blue-800",
    ],
    secondary: [
      "text-gray-900 bg-white border border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600",
      "hover:bg-gray-100 hover:text-blue-700 dark:hover:text-white dark:hover:bg-gray-700",
      "focus:ring-gray-200 dark:focus:ring-gray-700",
    ],
    success: [
      "text-white bg-green-700 dark:bg-green-600",
      "hover:bg-green-800 dark:hover:bg-green-700",
      "focus:ring-green-300 dark:focus:ring-green-800",
    ],
    warning: [
      "text-white bg-yellow-400",
      "hover:bg-yellow-500",
      "focus:ring-yellow-300 dark:focus:ring-yellow-900",
    ],
    danger: [
      "text-white bg-red-700 dark:bg-red-600",
      "hover:bg-red-800 dark:hover:bg-red-700",
      "focus:ring-red-300 dark:focus:ring-red-900",
    ],
    light: [
      "text-gray-900 bg-white border border-gray-300 dark:bg-gray-800 dark:text-white dark:border-gray-600",
      "hover:bg-gray-100 dark:hover:bg-gray-700",
      "focus:ring-gray-200 dark:focus:ring-gray-700",
    ],
    dark: [
      "text-white bg-gray-800 dark:bg-gray-800",
      "hover:bg-gray-900 dark:hover:bg-gray-700",
      "focus:ring-gray-300 dark:focus:ring-gray-700",
    ],
    outline: [
      "text-gray-900 border border-gray-800 dark:border-gray-600 dark:text-gray-400",
      "hover:text-white hover:bg-gray-900 dark:hover:text-white dark:hover:bg-gray-600",
      "focus:ring-gray-300 dark:focus:ring-gray-700",
    ],
  };

  const widthClass = $derived(fullWidth ? "w-full" : "");

  const allClasses = $derived([
    ...baseClasses,
    sizeClasses[size],
    ...variantClasses[variant],
    widthClass,
    customClass,
  ]
    .filter(Boolean)
    .join(" "));

  function handleClick() {
    if (disabled || loading) return;
    onclick?.();
  }
</script>

<button class={allClasses} {disabled} onclick={handleClick} type="button">
  {#if loading}
    <svg
      class="w-3 h-3 me-2 animate-spin"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 14 14"
    >
      <path
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M7 1L5.41 1.59A8.26 8.26 0 0 0 1.41 5L1 7l.59 1.59A8.26 8.26 0 0 0 5.41 12.41L7 13l1.59-.59A8.26 8.26 0 0 0 12.59 9L13 7l-.59-1.59A8.26 8.26 0 0 0 8.59 1.41L7 1Z"
      />
    </svg>
  {/if}
  {#if children}{@render (children as any)()}{/if}
</button>
