import React from 'react';

function HomePage({ onLogout }) {
  return (
    <div className="home-container">
      <div className="card">
        <h2>Welcome!</h2>
        <button onClick={onLogout}>Logout</button>
      </div>
    </div>
  );
}

export default HomePage;
