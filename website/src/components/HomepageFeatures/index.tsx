import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'What is OS-Lang?',
    description: (
      <>
        A high-performance systems programming language compiled directly to LLVM IR, 
        designed specifically for writing operating systems, kernels, and bare-metal drivers.
      </>
    ),
  },
  {
    title: 'Why OS-Lang?',
    description: (
      <>
        It merges the precise, low-level hardware control of C with the clean, modern 
        ergonomics and safety features of next-generation languages.
      </>
    ),
  },
  {
    title: 'Why use it?',
    description: (
      <>
        Say goodbye to complex linker scripts and inline assembly. Write pure, memory-safe code 
        with <code>@unsafe</code> boundaries, built-in hardware intrinsics, and zero-overhead abstractions.
      </>
    ),
  },
];

function Feature({title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md padding-vert--lg glass-panel" style={{borderRadius: '12px', margin: '10px 0', height: '100%'}}>
        <h3>{title}</h3>
        <p style={{color: '#a1a1aa'}}>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features} style={{padding: '4rem 0'}}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
