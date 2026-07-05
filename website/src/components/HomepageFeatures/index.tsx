import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Get Started',
    description: (
      <>
        Whether you're new to systems programming or an experienced kernel developer, it's easy to learn and use OS-Lang.
        <br/><br/>
        <a href="/docs/intro" style={{fontWeight: 'bold', color: 'var(--py-blue)'}}>Start with our Beginner’s Guide</a>
      </>
    ),
  },
  {
    title: 'Download',
    description: (
      <>
        OS-Lang compiler and tools are available for download for all platforms!
        <br/><br/>
        Latest: <a href="/docs/getting-started/installation" style={{fontWeight: 'bold', color: 'var(--py-blue)'}}>OS-Lang 1.0.0</a>
      </>
    ),
  },
  {
    title: 'Docs',
    description: (
      <>
        Documentation for OS-Lang's standard library, along with tutorials and guides, are available online.
        <br/><br/>
        <a href="/docs/intro" style={{fontWeight: 'bold', color: 'var(--py-blue)'}}>os-lang.dev/docs</a>
      </>
    ),
  },
  {
    title: 'Memory Safety',
    description: (
      <>
        Say goodbye to complex linker scripts and inline assembly. Write pure, memory-safe code 
        with <code>@unsafe</code> boundaries and zero-overhead abstractions.
      </>
    ),
  },
];

function Feature({title, description}) {
  return (
    <div className="featureCard">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features} style={{padding: '4rem 0'}}>
      <div className="container" style={{maxWidth: '1200px', margin: '0 auto'}}>
        <div className="featuresGrid">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
