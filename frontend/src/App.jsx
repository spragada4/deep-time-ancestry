import { useState } from "react";
import { milestones } from "./data/milestones";
import { yearsToGenerations, ancestorSlots, nearestMilestone } from "./lib/ancestry";
import "./App.css";

export default function App() {
  const [exponent, setExponent] = useState(2); // log scale: 10^2 = 100 years

  const yearsAgo = Math.round(10 ** exponent);
  const generations = yearsToGenerations(yearsAgo);
  const slots = ancestorSlots(generations);
  const milestone = nearestMilestone(milestones, yearsAgo);

  return (
    <main className="app">
      <h1>Deep Time Ancestry</h1>

      <label>
        Travel back: <strong>{yearsAgo.toLocaleString()} years</strong>
        <input
          type="range"
          min="1"
          max="6.9"
          step="0.01"
          value={exponent}
          onChange={(e) => setExponent(Number(e.target.value))}
        />
      </label>

      <section>
        <p>That's about <strong>{generations.toLocaleString()}</strong> generations ago.</p>
        <p>
          Ancestor slots:{" "}
          <strong>
            {slots !== null
              ? slots.toLocaleString()
              : "more than the humans who have ever lived"}
          </strong>
        </p>
        {slots === null && (
          <p className="note">
            This is pedigree collapse: the same people fill many slots in your family tree.
          </p>
        )}
      </section>

      <section className="milestone">
        <h2>Nearest milestone: {milestone.title}</h2>
        <p>About {milestone.yearsAgo.toLocaleString()} years ago. {milestone.text}</p>
      </section>
    </main>
  );
}