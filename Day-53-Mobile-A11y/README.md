# Day 53 — Mobile-First Design & Accessibility

> **Phase 7 — Full Stack Integration** | Day 53 of 180

---

## 📌 What I Learned Today

- Mobile-first: write for small screens first, enhance with md:/lg: prefixes
- No prefix = all screens, sm: = 640+, md: = 768+, lg: = 1024+
- Touch targets: minimum 44×44px (WCAG) → use min-h-[44px] min-w-[44px]
- viewport-fit=cover: extends background behind iOS notch/safe areas
- env(safe-area-inset-bottom): space above iOS home indicator
- Swipe gestures: track touchstart/touchmove/touchEnd x coordinates
- Threshold: trigger swipe only if dx > 50px (avoids accidental swipes)
- Cancel swipe if vertical movement exceeds horizontal (scrolling intent)
- prefers-reduced-motion: skip animations for users who opt out
- usePrefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)')
- ARIA roles: dialog, alert, status, navigation, tablist, tab, tabpanel
- aria-modal="true": tells screen reader content outside is inert
- aria-labelledby: reference another element's text as the label
- aria-invalid + aria-errormessage: form validation for screen readers
- aria-required="true": indicates required field to screen readers
- aria-live="polite": announce changes after user finishes their action
- aria-live="assertive": interrupt screen reader immediately (errors only)
- aria-pressed: toggle button state (selected/unselected)
- aria-current="page": active navigation item
- Focus trap: Tab cycles through focusable elements inside modal
- Focus return: restore focus to trigger element when modal closes
- sr-only: visually hidden but screen-reader accessible
- focus:not-sr-only: make sr-only visible when focused (skip link pattern)
- Skip link: first focusable element, jumps to #main-content
- Role=tablist/tab/tabpanel: accessible tab interface
- PWA manifest: name, icons, display:standalone, theme_color
- Service worker: stale-while-revalidate for static, network-only for API
- Lighthouse PWA audit: installable, offline, icons, manifest
- SkipLink: invisible until focused, floats above all content
- Line-clamp: text-clamp in Tailwind (webkit-line-clamp)
- WCAG AA contrast: 4.5:1 for normal text, 3:1 for large text

## 🔨 Project Built

**TaskMind Mobile + Accessible:**

**PWA:**
- manifest.json with icons, colors, shortcuts, standalone display
- Service worker: stale-while-revalidate caching strategy
- Offline API fallback with descriptive error response
- Meta tags for iOS and Android installation

**Mobile UI:**
- MobileNav: bottom navigation, 64px tap targets, primary FAB button
- Tab switcher: accessible tablist/tab/tabpanel with task counts
- TaskCardMobile: swipe left→delete, swipe right→done with animation
- Swipe cancellation if vertical movement > horizontal
- Reduced motion: skip animations if user prefers

**Accessibility:**
- SkipLink: first tab stop, jumps keyboard users to content
- LiveRegion: announces task CRUD actions to screen readers
- AccessibleModal: role=dialog, focus trap, Escape to close, focus return
- TaskFormMobile: labeled inputs, aria-invalid, aria-required, role=alert for errors
- Radio buttons for priority (not divs) — accessible by default
- ARIA counts in tab buttons (aria-label="3 tasks")
- All buttons have aria-label when icon-only
- Minimum 44px tap targets throughout

## 🚀 How to Run

```bash
cd Day-53-Mobile-A11y/frontend
npm install
npm run dev --host

# Test mobile: open DevTools → device toolbar → iPhone SE
# Test a11y: Tab through page keyboard-only
# Test PWA: Lighthouse → PWA audit
# Test screen reader: VoiceOver (macOS) + Safari
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)