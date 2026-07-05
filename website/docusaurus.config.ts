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
        defaultMode: 'dark',
        disableSwitch: true, // Force Dark Luxury
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'OS-Lang',
        items: [
          { type: 'docSidebar', sidebarId: 'tutorialSidebar', position: 'left', label: 'Documentation' },
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
