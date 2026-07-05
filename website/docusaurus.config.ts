import {themes as prismThemes} from 'prism-react-renderer';

import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'OS-Lang',
  tagline: 'The Next Generation of Systems Programming',
  favicon: 'img/favicon.ico',
  url: 'https://os-lang.dev',
  baseUrl: '/',
  organizationName: 'Techmastergojo', 
  projectName: 'os-lang', 
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  i18n: { defaultLocale: 'en', locales: ['en'] },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/Techmastergojo/os-lang/tree/main/website/',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
      colorMode: {
        defaultMode: 'light',
        disableSwitch: true, // Force Light theme as per python.org
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'OS-Lang',
        logo: {
          alt: 'OS-Lang Logo',
          src: 'img/logo.svg', // Will use text if logo isn't present, but keeping for standard format
        },
        items: [
          { type: 'docSidebar', sidebarId: 'tutorialSidebar', position: 'left', label: 'Documentation' },
          { to: '/downloads', label: 'Downloads', position: 'left' },
          { to: '/community', label: 'Community', position: 'left' },
          { href: 'https://github.com/Techmastergojo/os-lang', label: 'GitHub', position: 'right' },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Copyright © ${new Date().getFullYear()} Techmastergojo. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.dracula,
        darkTheme: prismThemes.dracula,
      },
    } satisfies Preset.ThemeConfig,
};

export default config;
