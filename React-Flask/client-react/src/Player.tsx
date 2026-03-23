import { useState } from "react";

function Player() {
  const [playing, setPlaying] = useState(false);

  const server = "http://192.168.0.47:5000";

  const togglePlay = () => {
    console.log("click"); // 👈 DEBUG

    if (playing) {
      fetch(`${server}/api/pause`);
    } else {
      fetch(`${server}/api/play`);
    }

    setPlaying(!playing);
  };

  return (
    <div className="player">
      <button onClick={togglePlay}>
        {playing ? "⏸" : "▶"}
      </button>
    </div>
  );
}

export default Player;