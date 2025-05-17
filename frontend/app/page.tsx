"use client";
import { useState } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentDatabase, setCurrentDatabase] = useState<string | null>(null);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);

  const runQuery = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: query }),
      });
      
      const data = await response.json();
      
      if (data.status === 'error') {
        setError(data.message);
      } else {
        setResults(data);
        
        // Update command history
        setCommandHistory(prev => [...prev, query]);
        
        // Update current database if USE DATABASE command was successful
        if (query.toUpperCase().startsWith('USE DATABASE') && data.status === 'success') {
          const dbName = query.toUpperCase().replace('USE DATABASE', '').trim();
          setCurrentDatabase(dbName);
        }
      }
    } catch (err) {
      setError('Failed to connect to server. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      runQuery();
    }
  };

  const renderTableData = (columns: string[], rows: any[]) => {
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-green-600">
              {columns.map((column: string) => (
                <th key={column} className="py-2 px-4 text-left text-green-300">{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: any[], i: number) => (
              <tr key={i} className="border-t border-green-600 hover:bg-green-900/20">
                {row.map((value: any, j: number) => (
                  <td key={j} className="py-2 px-4 text-green-200">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderDatabasesList = (databases: string[]) => {
    return (
      <div>
        <h3 className="text-xl mb-2">Databases:</h3>
        {databases.length === 0 ? (
          <p>No databases found</p>
        ) : (
          <ul className="list-disc list-inside space-y-1 pl-4">
            {databases.map((db, i) => (
              <li key={i} className={currentDatabase === db ? "text-green-400 font-bold" : ""}>
                {db} {currentDatabase === db && "(active)"}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  };

  const renderTablesList = (tables: {relational: string[], vector: string[]}) => {
    return (
      <div>
        <h3 className="text-xl mb-2">Tables:</h3>
        
        <div className="mb-4">
          <h4 className="text-lg font-medium text-green-400">Relational Tables:</h4>
          {tables.relational.length === 0 ? (
            <p className="text-green-200 italic">No relational tables found</p>
          ) : (
            <ul className="list-disc list-inside space-y-1 pl-4">
              {tables.relational.map((table, i) => (
                <li key={i}>{table}</li>
              ))}
            </ul>
          )}
        </div>
        
        <div>
          <h4 className="text-lg font-medium text-green-400">Vector Tables:</h4>
          {tables.vector.length === 0 ? (
            <p className="text-green-200 italic">No vector tables found</p>
          ) : (
            <ul className="list-disc list-inside space-y-1 pl-4">
              {tables.vector.map((table, i) => (
                <li key={i}>{table}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  };

  const renderVectorSearchResults = (results: Array<{index: number, similarity: number, metadata: any}>) => {
    return (
      <div>
        <h3 className="text-xl mb-2">Vector Search Results:</h3>
        {results.length === 0 ? (
          <p>No matching vectors found</p>
        ) : (
          <div className="space-y-2">
            {results.map((result, i) => (
              <div key={i} className="border border-green-700 rounded p-3 bg-green-900/20">
                <div className="flex justify-between">
                  <span className="font-medium">Index: {result.index}</span>
                  <span className="font-medium">Similarity: {result.similarity.toFixed(4)}</span>
                </div>
                {result.metadata && Object.keys(result.metadata).length > 0 && (
                  <div className="mt-2">
                    <h5 className="text-sm text-green-400">Metadata:</h5>
                    <pre className="text-xs bg-black/50 p-2 rounded mt-1 overflow-x-auto">
                      {JSON.stringify(result.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderResults = () => {
    if (!results) return null;
    
    // Display results based on the response and command type
    if (results.status === 'success') {
      // For database operations
      if (results.message && results.message.includes('Database')) {
        return <p className="text-green-300">{results.message}</p>;
      }
      
      // For table operations
      if (results.message && results.message.includes('Table')) {
        return <p className="text-green-300">{results.message}</p>;
      }
      
      // Show databases list
      if (results.databases) {
        return renderDatabasesList(results.databases);
      }
      
      // Show tables list
      if (results.tables) {
        return renderTablesList(results.tables);
      }
      
      // For data insertion
      if (results.message && results.message.includes('inserted')) {
        return <p className="text-green-300">{results.message}</p>;
      }
      
      // For SELECT results
      if (results.columns && results.rows) {
        return (
          <div>
            <h3 className="text-xl mb-2">Query Results:</h3>
            {results.rows.length === 0 ? (
              <p className="text-green-200 italic">No results found</p>
            ) : (
              renderTableData(results.columns, results.rows)
            )}
          </div>
        );
      }
      
      // For vector search results
      if (results.results) {
        return renderVectorSearchResults(results.results);
      }
    }
    
    // Default: just show the raw response
    return (
      <div>
        <h3 className="text-xl mb-2">Response:</h3>
        <pre className="bg-black/50 p-3 rounded text-green-200 overflow-x-auto">
          {JSON.stringify(results, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-black text-green-400 px-4 py-12 font-mono">
      <h1 className="text-6xl font-bold mb-4 text-center border-b border-green-500 pb-2">
        MascotDB
      </h1>
      <p className="text-lg mb-2 text-center text-green-300 max-w-xl">
        Welcome to <span className="text-white font-bold">Mascot</span>, a lightweight RDBMS with vector capabilities.
      </p>
      
      {currentDatabase && (
        <p className="mb-6 text-center">
          Current database: <span className="text-white font-bold">{currentDatabase}</span>
        </p>
      )}

      <div className="w-full max-w-2xl bg-[#0d0d0d] p-6 rounded-lg border border-green-500 shadow-lg">
        <h2 className="text-2xl mb-4 font-semibold text-green-400">Execute Command</h2>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. CREATE DATABASE mydb"
          className="w-full bg-black text-green-300 border border-green-600 p-3 rounded-lg mb-4 resize-none h-32"
        ></textarea>
        <div className="flex justify-between items-center">
          <button 
            onClick={runQuery}
            disabled={loading}
            className="bg-green-600 hover:bg-green-500 text-black font-bold py-2 px-4 rounded disabled:opacity-50">
            {loading ? 'Running...' : 'Run Command'}
          </button>
          <span className="text-green-400 text-sm">Press Ctrl+Enter to run</span>
        </div>
      </div>

      {error && (
        <div className="mt-6 w-full max-w-2xl p-4 bg-red-900/30 border border-red-800 rounded-lg text-red-300">
          <p className="font-bold">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {results && (
        <div className="mt-6 w-full max-w-2xl p-4 bg-[#0d0d0d] border border-green-500 rounded-lg">
          {renderResults()}
        </div>
      )}

      <div className="mt-8 w-full max-w-2xl">
        <h3 className="text-xl mb-2 text-green-400">Example Commands:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-1 text-green-300">Database Operations</h4>
            <ul className="list-disc list-inside space-y-1 text-green-200 text-sm">
              <li><code>CREATE DATABASE mydb</code></li>
              <li><code>USE DATABASE mydb</code></li>
              <li><code>SHOW DATABASES</code></li>
              <li><code>DROP DATABASE mydb</code></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium mb-1 text-green-300">Table Operations</h4>
            <ul className="list-disc list-inside space-y-1 text-green-200 text-sm">
              <li><code>SHOW TABLES</code></li>
              <li><code>CREATE TABLE users (id, name, email)</code></li>
              <li><code>DROP TABLE users</code></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium mb-1 text-green-300">Data Operations</h4>
            <ul className="list-disc list-inside space-y-1 text-green-200 text-sm">
              <li><code>INSERT INTO users VALUES (1, "John", "john@example.com")</code></li>
              <li><code>SELECT * FROM users</code></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium mb-1 text-green-300">Vector Operations</h4>
            <ul className="list-disc list-inside space-y-1 text-green-200 text-sm">
              <li><code>CREATE VECTOR TABLE embeddings DIMENSION 3</code></li>
              <li><code>INSERT VECTOR INTO embeddings VALUES [0.1, 0.2, 0.3] WITH METADATA ${JSON.stringify({"text": "example"})}</code></li>
              <li><code>VECTOR SEARCH embeddings QUERY [0.1, 0.2, 0.3] TOP 5</code></li>
            </ul>
          </div>
        </div>
      </div>

      {commandHistory.length > 0 && (
        <div className="mt-8 w-full max-w-2xl">
          <h3 className="text-xl mb-2 text-green-400">Command History:</h3>
          <div className="bg-[#0d0d0d] border border-green-700 rounded-lg p-2 max-h-40 overflow-y-auto">
            <ul className="space-y-1">
              {commandHistory.map((cmd, i) => (
                <li key={i} className="text-green-200 text-sm font-mono cursor-pointer hover:text-white hover:bg-green-900/20 px-2 py-1 rounded"
                    onClick={() => setQuery(cmd)}>
                  {cmd}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <footer className="mt-10 text-sm text-green-500 opacity-70">
        Built with ♥ by Sai
      </footer>
    </main>
  );
}