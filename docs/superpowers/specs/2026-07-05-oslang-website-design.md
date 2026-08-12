# OS-Lang Website Design Specification

## 1. Overview
The goal is to build a highly professional, "Dark Luxury" documentation website and marketing landing page for the OS-Lang systems programming language. The site will serve as the primary resource for developers to learn what OS-Lang is, why it exists, and how to start building operating systems with it.

## 2. Technology Stack
*   **Framework:** Docusaurus (v3) - React-based static site generator optimized for documentation.
*   **Styling:** Custom CSS tailored to a "Dark Luxury" aesthetic (deep blacks, glassmorphism, subtle glowing accents).
*   **Syntax Highlighting:** Prism.js configured for a dark IDE-like experience.

## 3. Landing Page Architecture (`src/pages/index.js`)
The home page will act as a premium marketing funnel to guide users to the documentation.
*   **Hero Section:** 
    *   Headline: "OS-Lang: The Next Generation of Systems Programming"
    *   Call-to-Action Buttons: "Get Started" (Primary Glow) and "Read the Docs" (Secondary Glass).
*   **Value Proposition (Features Grid):**
    *   What is OS-Lang?
    *   Why OS-Lang?
    *   Why use OS-Lang? (Benefits over legacy tools).
*   **Code Showcase:** Side-by-side view showing a beautiful OS-Lang snippet (e.g., hardware interrupts or pattern matching) next to an explanation of the feature.

## 4. Documentation Structure (`docs/`)
*   **Introduction**
    *   `what-is-oslang.md`: Overview of the language.
    *   `benefits.md`: Core benefits of OS-Lang.
    *   `comparison.md`: Detailed comparison against C (memory safety, modern syntax) and Rust (simpler learning curve, no aggressive borrow checker for Ring 0).
*   **Getting Started**
    *   `installation.md`: Guide for `pip install oslang`.
    *   `vs-code-extension.md`: Guide to setting up the syntax highlighter.
    *   `environment-setup.md`: Guide to setting up QEMU and the build pipeline.
*   **Language Guide**
    *   `syntax-basics.md`
    *   `memory-safety.md` (`@unsafe`)
    *   `hardware-alignment.md` (`@packed` & `sizeof`)
    *   `pattern-matching.md` (`match`)
*   **Examples**
    *   `ascii-keyboard.md`: A deep-dive tutorial on creating an ASCII keyboard driver using port I/O (`inb`) and interrupts.

## 5. Development Workflow
1.  Initialize Docusaurus project in the `website/` folder.
2.  Clear default Docusaurus boilerplate and apply global CSS variables for Dark Luxury theme.
3.  Implement the React-based Landing Page.
4.  Write the markdown documentation files.
5.  Validate local build and prepare for deployment.
