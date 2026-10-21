import type { ReactNode } from 'react';

export default function DocsPage() {
  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Documentation</h1>
        <p className="page-subtitle">Methods, data dictionary, API reference, and reproducibility guide.</p>
      </div>

      {/* TOC */}
      <div className="card card-sm" style={{ marginBottom:24 }}>
        <div className="section-label" style={{ marginBottom:8 }}>Contents</div>
        <div style={{ display:'flex', gap:16, flexWrap:'wrap', fontSize:'0.82rem' }}>
          {['Methods','Data Dictionary','Statistical Pipeline','Reproducibility','API Reference','Limitations'].map(s => (
            <a key={s} href={`#${s.toLowerCase().replace(/ /g,'-')}`} style={{ color:'var(--color-accent)' }}>{s}</a>
          ))}
        </div>
      </div>

      <Section id="methods" title="Methods">
        <p>MANAS ingests publicly available post-mortem human brain research data and applies
        reproducible statistical analysis to identify brain-region-level differences between
        Alzheimer&apos;s disease and control cohorts.</p>
        <p style={{ marginTop:12 }}>The V1 analysis pipeline uses a normality-adaptive approach:
        each brain region is tested independently, with the appropriate parametric or
        non-parametric test selected based on Shapiro-Wilk (n ≤ 50) or D&apos;Agostino-Pearson
        (n &gt; 50) normality tests. Effect sizes are calculated with bootstrap confidence
        intervals for robustness. Multiple testing is corrected using the Benjamini-Hochberg
        False Discovery Rate procedure (α = 0.05).</p>
      </Section>

      <Section id="data-dictionary" title="Data Dictionary">
        <Table headers={['Variable','Dataset','Description','Unit']} rows={[
          ['ihc_at8_ffpe','Allen Aging','Phosphorylated tau (AT8 antibody) density by IHC','fraction area'],
          ['ihc_a_beta_ffpe','Allen Aging','Amyloid-β density by immunohistochemistry','fraction area'],
          ['tau_ng_per_mg','Allen Aging','Total tau protein (Luminex)','ng/mg tissue'],
          ['ptau_ng_per_mg','Allen Aging','Phosphorylated tau (Luminex)','ng/mg tissue'],
          ['ab42_pg_per_mg','Allen Aging','Amyloid-β42 peptide (Luminex)','pg/mg tissue'],
          ['ihc_a_syn','Allen Aging','α-synuclein density by IHC','fraction area'],
          ['bdnf_pg_per_mg','Allen Aging','Brain-derived neurotrophic factor','pg/mg tissue'],
          ['isoprostane_pg_per_mg','Allen Aging','8-isoprostane (oxidative stress marker)','pg/g tissue'],
          ['CDR','OASIS-1/2','Clinical Dementia Rating','0–3 ordinal'],
          ['MMSE','OASIS-1/2','Mini-Mental State Examination','0–30 score'],
          ['nWBV','OASIS-1/2','Normalised Whole Brain Volume','proportion (MRI-derived)'],
          ['eTIV','OASIS-1/2','Estimated Total Intracranial Volume','mm³ (MRI-derived)'],
        ]} />
      </Section>

      <Section id="statistical-pipeline" title="Statistical Pipeline">
        <ol style={{ paddingLeft:20, lineHeight:2.2, fontSize:'0.85rem', color:'var(--color-text-2)' }}>
          <li><strong>Data loading</strong> — quality-flagged measurements (PASS or WARNING) for AD and CONTROL subjects</li>
          <li><strong>Normality testing</strong> — Shapiro-Wilk (n ≤ 50) or D&apos;Agostino-Pearson (n &gt; 50) per group</li>
          <li><strong>Test selection</strong> — Student&apos;s t (equal variance), Welch&apos;s t (unequal), or Mann-Whitney U (non-parametric)</li>
          <li><strong>Effect size</strong> — Hedges&apos; g (Cohen&apos;s d corrected) or rank-biserial correlation r</li>
          <li><strong>Bootstrap CI</strong> — 1000 iterations, percentile method, 95% confidence, reproducible seed</li>
          <li><strong>FDR correction</strong> — Benjamini-Hochberg across all tested regions, monotone-enforced</li>
          <li><strong>Result storage</strong> — all fields stored; insufficient data regions retained with flag</li>
        </ol>
      </Section>

      <Section id="reproducibility" title="Reproducibility">
        <p style={{ fontSize:'0.85rem', color:'var(--color-text-2)', lineHeight:1.7 }}>
          Every analysis run in MANAS is assigned a permanent identifier (e.g.{' '}
          <code style={{ fontFamily:'var(--font-mono)', fontSize:'0.8rem' }}>MANAS-AD-2026-00001</code>).
          The following are stored and queryable at any time:
        </p>
        <Table headers={['Recorded field','Description']} rows={[
          ['analysis_run_id','Permanent MANAS run identifier'],
          ['version_id','Exact dataset version used (with checksum)'],
          ['ingestion_version','Code version of the ingestion pipeline'],
          ['parameters','Complete JSON of all analysis parameters'],
          ['random_seed','Seed for all stochastic operations (default: 42)'],
          ['covariates','List of covariates requested'],
          ['software_env','Python, scipy, numpy, pandas versions'],
          ['code_commit','Git SHA of MANAS code at run time'],
          ['statistical_method','Full description of the test actually used'],
        ]} />
      </Section>

      <Section id="api-reference" title="API Reference">
        <p style={{ fontSize:'0.85rem', color:'var(--color-text-muted)', marginBottom:12 }}>
          Interactive API documentation: <a href="http://localhost:8005/api/docs" target="_blank" rel="noreferrer" style={{ color:'var(--color-accent)' }}>http://localhost:8005/api/docs ↗</a>
        </p>
        <Table headers={['Endpoint','Method','Description']} rows={[
          ['/api/health','GET','System health and DB status'],
          ['/api/datasets/','GET','List all registered datasets'],
          ['/api/regions/','GET','Paginated brain region list (search, filter)'],
          ['/api/regions/{id}','GET','Region detail with analysis results'],
          ['/api/analyses/','GET','List analysis runs'],
          ['/api/analyses/','POST','Submit new analysis job'],
          ['/api/analyses/{id}','GET','Full analysis run detail + provenance'],
          ['/api/analyses/{id}/results','GET','Paginated per-region results'],
          ['/api/literature/','GET','Verified paper registry'],
          ['/api/literature/evidence','GET','Structured evidence claims'],
          ['/api/ingestion/allen-aging','POST','Trigger Allen Aging ingestion'],
          ['/api/ingestion/allen-atlas','POST','Trigger brain atlas ingestion'],
          ['/api/ingestion/status/{id}','GET','Processing run status'],
        ]} />
      </Section>

      <Section id="limitations" title="Limitations">
        <ul style={{ paddingLeft:20, lineHeight:2.2, fontSize:'0.85rem', color:'var(--color-text-2)' }}>
          <li><strong>Sample size</strong>: Allen Aging has 107 donors in 4 regions — small by modern standards</li>
          <li><strong>Regional coverage</strong>: Only 4 brain regions sampled (HIP, TCx, PCx, FWM) — not a whole-brain survey</li>
          <li><strong>Post-mortem bias</strong>: All Allen data is from post-mortem tissue — does not reflect in-vivo dynamics</li>
          <li><strong>Cross-sectional only</strong>: V1 analysis is cross-sectional; no causal or longitudinal inference</li>
          <li><strong>Diagnosis heterogeneity</strong>: DSM-IV diagnosis is the primary label; neuropathological confirmation varies</li>
          <li><strong>No MRI</strong>: OASIS nWBV is a pre-computed scalar; raw MRI is not processed</li>
          <li><strong>Confounders</strong>: Age, sex are noted as covariates but full covariate-adjusted GLM is V2</li>
          <li><strong>Replication</strong>: All findings require independent replication before scientific conclusions can be drawn</li>
        </ul>
        <div style={{ marginTop:16, padding:12, background:'var(--color-surface-2)', borderRadius:4, fontSize:'0.78rem', color:'var(--color-text-muted)' }}>
          <strong>Scientific disclaimer:</strong> MANAS is a computational research platform. Results are
          statistical associations from public research datasets. They do not constitute medical
          diagnosis, clinical advice, or proof of biological causation.
        </div>
      </Section>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} style={{ marginBottom:40 }}>
      <h2 style={{ fontSize:'1.1rem', fontWeight:700, marginBottom:16, paddingBottom:8,
        borderBottom:'2px solid var(--color-border)', color:'var(--color-text)' }}>{title}</h2>
      {children}
    </section>
  );
}

function Table({ headers, rows }: { headers:string[]; rows:string[][] }) {
  return (
    <div className="table-wrap" style={{ marginTop:12 }}>
      <table className="data-table">
        <thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} style={{ fontFamily:j===0?'var(--font-mono)':undefined, fontSize:'0.82rem' }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
