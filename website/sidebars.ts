import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'comparison',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/environment-setup',
      ],
    },
    {
      type: 'category',
      label: 'Language Guide',
      items: [
        'language-guide/memory-safety',
        'language-guide/hardware-alignment',
        'language-guide/pattern-matching',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/ascii-keyboard',
      ],
    },
  ],
};

export default sidebars;
