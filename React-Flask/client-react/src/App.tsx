import { useState, useEffect, use } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

import Player from "./Player";

function App() {
  return (
    <>
      <section id="center">
        <h1>React con Python</h1>
      </section>

      {/* Aquí lo integras normal */}
      <Player />
    </>
  );
}

export default App
