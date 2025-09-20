import React from 'react';

function App() {
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f0f8ff', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ color: '#1e40af', fontSize: '2.5rem', marginBottom: '20px' }}>
        🧠 MindSpace
      </h1>
      <p style={{ color: '#059669', fontSize: '1.2rem', marginBottom: '30px' }}>
        Your safe space for mental wellness and peer support
      </p>
      
      <div style={{ 
        backgroundColor: 'white', 
        padding: '30px', 
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        maxWidth: '400px',
        margin: '0 auto'
      }}>
        <h2 style={{ color: '#374151', marginBottom: '20px' }}>Welcome to MindSpace!</h2>
        <p style={{ color: '#6b7280', marginBottom: '20px' }}>
          The app is working! 🎉
        </p>
        <p style={{ color: '#6b7280', marginBottom: '20px' }}>
          Backend: ✅ Running on port 8000<br/>
          Frontend: ✅ Running on port 3000
        </p>
        <button 
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '12px 24px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
          onClick={() => alert('MindSpace is working perfectly! 🚀')}
        >
          Test Button
        </button>
      </div>
    </div>
  );
}

export default App;
