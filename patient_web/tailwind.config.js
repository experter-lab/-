/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          soft: "hsl(var(--primary-soft))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // 辅助色阶, 用于状态可视化
        info: {
          DEFAULT: "hsl(200 90% 45%)",
          soft: "hsl(200 90% 95%)",
          ink: "hsl(200 90% 25%)",
        },
        warn: {
          DEFAULT: "hsl(35 95% 50%)",
          soft: "hsl(40 95% 94%)",
          ink: "hsl(30 90% 28%)",
        },
        danger: {
          DEFAULT: "hsl(0 75% 50%)",
          soft: "hsl(0 80% 96%)",
          ink: "hsl(0 75% 30%)",
        },
        ok: {
          DEFAULT: "hsl(160 84% 32%)",
          soft: "hsl(152 60% 94%)",
          ink: "hsl(160 70% 22%)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        "2xl": "calc(var(--radius) + 6px)",
        "3xl": "calc(var(--radius) + 12px)",
      },
      fontSize: {
        // 病人友好: 默认字号比常规大
        xs: ["0.8125rem", { lineHeight: "1.5" }],
        sm: ["0.9375rem", { lineHeight: "1.55" }],
        base: ["1.0625rem", { lineHeight: "1.6" }],
        lg: ["1.25rem", { lineHeight: "1.5" }],
        xl: ["1.5rem", { lineHeight: "1.35" }],
        "2xl": ["1.875rem", { lineHeight: "1.25" }],
        "3xl": ["2.25rem", { lineHeight: "1.15" }],
        "4xl": ["3rem", { lineHeight: "1.1" }],
        "5xl": ["3.75rem", { lineHeight: "1" }],
      },
      boxShadow: {
        // 更精致的层次, 比 shadcn 默认柔
        soft: "0 1px 2px 0 hsl(160 30% 10% / 0.04), 0 1px 3px 0 hsl(160 30% 10% / 0.05)",
        card: "0 2px 4px -1px hsl(160 30% 10% / 0.06), 0 4px 12px -2px hsl(160 30% 10% / 0.08)",
        elevated:
          "0 6px 14px -4px hsl(160 40% 10% / 0.10), 0 16px 32px -8px hsl(160 40% 10% / 0.12)",
        glow: "0 0 0 1px hsl(var(--primary) / 0.15), 0 6px 18px -4px hsl(var(--primary) / 0.35)",
        inner: "inset 0 1px 2px 0 hsl(160 30% 10% / 0.06)",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at 20% 20%, hsl(var(--primary) / 0.08), transparent 40%), radial-gradient(circle at 80% 0%, hsl(200 90% 60% / 0.06), transparent 35%)",
        "primary-sheen":
          "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(168 78% 38%) 100%)",
        "card-sheen":
          "linear-gradient(180deg, hsl(var(--card)) 0%, hsl(150 25% 99%) 100%)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.95)", opacity: "0.7" },
          "70%": { transform: "scale(1.4)", opacity: "0" },
          "100%": { transform: "scale(1.4)", opacity: "0" },
        },
        "soft-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "robot-bob": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-3px)" },
        },
        "spin-slow": {
          to: { transform: "rotate(360deg)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in-up": "fade-in-up 0.35s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in": "fade-in 0.4s ease-out",
        "pulse-ring": "pulse-ring 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite",
        "soft-pulse": "soft-pulse 2.4s ease-in-out infinite",
        shimmer: "shimmer 2.2s linear infinite",
        "robot-bob": "robot-bob 1.6s ease-in-out infinite",
        "spin-slow": "spin-slow 8s linear infinite",
        marquee: "marquee 35s linear infinite",
      },
    },
  },
  plugins: [import("tailwindcss-animate")],
}
