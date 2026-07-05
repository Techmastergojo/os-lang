import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className="heroBanner">
      <div className="heroContainer">
        <div className="heroText">
          <h1 className="heroTitle">os-lang</h1>
          <p className="heroSubtitle">
            {siteConfig.tagline}.<br/>
            An intuitive, memory-safe, and highly optimized systems language.
          </p>
          <div className="buttons">
            <Link
              className="button button--py-yellow"
              to="/docs/getting-started/installation">
              Download OS-Lang 1.0.0
            </Link>
            <Link
              className="button button--py-blue"
              to="/docs/intro">
              Documentation
            </Link>
          </div>
        </div>
        <div className="heroCode">
          <h3>>_ Launch Interactive Shell</h3>
          <pre>
<code><span className="comment"># Simple memory safe pointer</span>
<span className="keyword">let</span> ptr: *u8 = <span className="keyword">@unsafe</span> &#123;
    ALLOCATOR.alloc(1024)
&#125;;

<span className="comment"># Zero-cost hardware mapping</span>
<span className="keyword">@packed</span>(1)
<span className="keyword">struct</span> IDTEntry &#123;
    base_low: u16,
    selector: u16,
&#125;
</code>
          </pre>
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
