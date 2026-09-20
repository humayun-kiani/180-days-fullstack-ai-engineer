// frontend/src/components/SkipLink.jsx

/**
 * Skip navigation link — essential for keyboard accessibility.
 *
 * Visually hidden until focused with the Tab key.
 * Allows keyboard users to skip repetitive navigation
 * and jump directly to the main page content.
 */
export default function SkipLink() {
  return (
    <a
      href="#main-content"
      className="
        sr-only
        focus:not-sr-only
        focus:fixed
        focus:top-4
        focus:left-4
        focus:z-[100]
        focus:px-4
        focus:py-2
        focus:bg-blue-600
        focus:text-white
        focus:rounded-lg
        focus:font-medium
        focus:text-sm
        focus:shadow-lg
        focus:outline-none
        focus:ring-2
        focus:ring-white
        focus:ring-offset-2
        focus:ring-offset-blue-600
      "
    >
      Skip to main content
    </a>
  );
}