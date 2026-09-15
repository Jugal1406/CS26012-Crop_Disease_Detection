import { Link } from "react-router-dom";

function Home() {
  return (
    <div>
      <h1>Crop Disease Detection</h1>

      <p>
        Detect plant diseases using an image of the crop leaf.
      </p>

      <Link to="/diagnose">
        Start Diagnosis
      </Link>
    </div>
  );
}

export default Home;