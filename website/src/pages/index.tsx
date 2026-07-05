import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className="heroBanner">
      <div className="container">
        <h1 className="heroTitle">{siteConfig.title}</h1>
        <p className="heroSubtitle">{siteConfig.tagline}</p>
        <div className="buttons">
          <Link
            className="button button--lg button--glow"
            to="/docs/intro">
            Get Started
          </Link>
          <Link
            className="button button--secondary button--outline button--lg glass-panel"
            to="/docs/intro"
            style={{ marginLeft: '1rem' }}>
            Read the Docs
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} | Systems Programming`}
      description="The next generation of systems programming languages">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
