/**
 * Central Lenis + GSAP Motion System
 * Coordinates smooth scrolling (Lenis) with scroll-linked animation (ScrollTrigger)
 * and component micro-interactions (GSAP).
 */

import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

// Configure standard GSAP defaults for calm, professional motion
gsap.defaults({
  ease: 'power3.out',
  duration: 0.65,
});

let lenisInstance = null;
let tickerCallback = null;
let isInitialized = false;

/**
 * Check if the user has requested reduced motion.
 */
export function isReducedMotion() {
  if (typeof window === 'undefined') return true;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Initialize the singleton Lenis smooth scrolling instance and bind to GSAP ticker.
 * Safe against React StrictMode duplicate invocations.
 */
export function initSmoothScroll() {
  if (typeof window === 'undefined') return () => {};
  if (isReducedMotion()) return () => {};

  if (!isInitialized && !lenisInstance) {
    lenisInstance = new Lenis({
      lerp: 0.09,
      smoothWheel: true,
      wheelMultiplier: 0.95,
      touchMultiplier: 1.5,
      autoResize: true,
    });

    // Update ScrollTrigger on Lenis scroll
    lenisInstance.on('scroll', ScrollTrigger.update);

    // Sync Lenis RAF into GSAP's central ticker
    tickerCallback = (time) => {
      if (lenisInstance) {
        lenisInstance.raf(time * 1000);
      }
    };
    gsap.ticker.add(tickerCallback);
    gsap.ticker.lagSmoothing(0);

    isInitialized = true;
  }

  // Return teardown function
  return () => {
    // Only teardown if explicitly called
  };
}

/**
 * Destroy the Lenis instance and remove ticker binding.
 */
export function destroySmoothScroll() {
  if (tickerCallback) {
    gsap.ticker.remove(tickerCallback);
    tickerCallback = null;
  }
  if (lenisInstance) {
    lenisInstance.destroy();
    lenisInstance = null;
  }
  isInitialized = false;
}

/**
 * Smoothly scroll to a specific target or position.
 */
export function scrollTo(target, options = {}) {
  if (isReducedMotion() || !lenisInstance) {
    if (typeof target === 'string') {
      const el = document.querySelector(target);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (typeof target === 'number') {
      window.scrollTo({ top: target, behavior: 'smooth' });
    }
    return;
  }
  lenisInstance.scrollTo(target, {
    offset: options.offset ?? 0,
    duration: options.duration ?? 1.1,
    easing: options.easing,
  });
}

/**
 * Subtle entrance animation for a container or page view.
 * Animate main content and smoothly staggers child cards.
 */
export function animatePageEntrance(containerEl) {
  if (!containerEl || isReducedMotion()) return;

  const ctx = gsap.context(() => {
    // 1. Animate main view container
    gsap.fromTo(
      containerEl,
      { opacity: 0, y: 8 },
      { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', clearProps: 'transform' }
    );

    // 2. Subtle stagger on immediate child cards/KPI items (limited to first 12 items)
    const cards = containerEl.querySelectorAll(
      '.stat-card, .module-card, .kpi-card, .analytics-chart-card, .doc-card, .source-card'
    );
    if (cards && cards.length > 0 && cards.length <= 16) {
      gsap.fromTo(
        cards,
        { opacity: 0, y: 6 },
        {
          opacity: 1,
          y: 0,
          duration: 0.35,
          stagger: 0.04,
          ease: 'power2.out',
          clearProps: 'transform',
        }
      );
    }
  }, containerEl);

  return () => ctx.revert();
}

/**
 * Staggered entrance for a group of cards, rows, or list items.
 */
export function animateStaggerEntrance(containerEl, itemSelector) {
  if (!containerEl || isReducedMotion()) return;

  const ctx = gsap.context(() => {
    const items = containerEl.querySelectorAll(itemSelector);
    if (!items.length) return;

    gsap.fromTo(
      items,
      { opacity: 0, y: 6 },
      {
        opacity: 1,
        y: 0,
        duration: 0.32,
        stagger: 0.04,
        ease: 'power2.out',
        clearProps: 'transform',
      }
    );
  }, containerEl);

  return () => ctx.revert();
}

/**
 * Register subtle scroll-linked reveal triggers for below-the-fold cards/sections.
 */
export function registerScrollTriggers(containerEl, selector = '.scroll-reveal') {
  if (!containerEl || isReducedMotion()) return () => {};

  const ctx = gsap.context(() => {
    const elements = containerEl.querySelectorAll(selector);
    elements.forEach((el) => {
      gsap.fromTo(
        el,
        { opacity: 0, y: 12 },
        {
          opacity: 1,
          y: 0,
          duration: 0.45,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: el,
            start: 'top 90%',
            toggleActions: 'play none none none',
          },
          clearProps: 'transform',
        }
      );
    });
  }, containerEl);

  return () => ctx.revert();
}

export { gsap, ScrollTrigger };
export default {
  initSmoothScroll,
  destroySmoothScroll,
  scrollTo,
  animatePageEntrance,
  animateStaggerEntrance,
  registerScrollTriggers,
  isReducedMotion,
  gsap,
  ScrollTrigger,
};
