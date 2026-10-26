export default function Home() {
  return (
    <div className="empty">
      <div className="khatam">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#b0842a" strokeWidth="1.1">
          <rect x="6" y="6" width="12" height="12" />
          <rect x="6" y="6" width="12" height="12" transform="rotate(45 12 12)" />
        </svg>
      </div>
      <h2>Pick a table</h2>
      <p>Tables are what agents query. Describe each table's grain, its columns' meaning, synonyms and allowed values, then publish it so agents can use it.</p>
    </div>
  );
}
