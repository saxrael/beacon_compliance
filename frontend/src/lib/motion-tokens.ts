/**
 * Motion Tokens and Physics Presets for Beacon Compliance (motion-advanced)
 */

export const springs = {
  gentle: { type: "spring" as const, stiffness: 180, damping: 24, mass: 1 },
  snappy: { type: "spring" as const, stiffness: 350, damping: 28, mass: 0.8 },
  bouncy: { type: "spring" as const, stiffness: 450, damping: 20, mass: 0.7 },
  release: { type: "spring" as const, stiffness: 300, damping: 30 },
  slow: { type: "spring" as const, stiffness: 120, damping: 26 },
};

export const motionTokens = {
  duration: {
    instant: 0.1,
    fast: 0.2,
    normal: 0.35,
    slow: 0.55,
    crawl: 1.2,
  },
  easing: {
    smooth: [0.25, 0.1, 0.25, 1.0] as [number, number, number, number],
    enter: [0.0, 0.0, 0.2, 1.0] as [number, number, number, number],
    exit: [0.4, 0.0, 1.0, 1.0] as [number, number, number, number],
  },
  scale: {
    hover: 1.015,
    press: 0.98,
    pop: 1.04,
  },
  distance: {
    sm: 8,
    md: 16,
    lg: 24,
    xl: 40,
  },
} as const;

export const containerStaggerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

export const itemFadeUpVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: springs.gentle,
  },
};

export const cardHoverVariants = {
  initial: { y: 0, scale: 1 },
  hover: { y: -2, scale: 1.008, transition: springs.snappy },
  tap: { y: 0, scale: 0.985, transition: springs.snappy },
};
