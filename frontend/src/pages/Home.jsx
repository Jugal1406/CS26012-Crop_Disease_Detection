import { Link } from "react-router-dom";

function Home() {
  return (
    <div>
      <nav>
        <h2>Crop Disease Detection</h2>

        <div>
          <Link to="/">Home</Link>
          {" | "}
          <Link to="/login">Login</Link>
        </div>
      </nav>

      <main>
        <h1>Detect Crop Diseases Easily</h1>

        <p>
          Upload an image of a crop leaf and get a disease prediction
          with a confidence score.
        </p>

        <Link to="/diagnose">
          <button>Start Diagnosis</button>
        </Link>
      </main>

      <section>
        <h2>Supported Crops</h2>

        <div>
          <h3>🥔 Potato</h3>
          <p>Upload a potato leaf image for disease detection.</p>
        </div>

        <div>
          <h3>🥜 Groundnut</h3>
          <p>Upload a groundnut leaf image for disease detection.</p>
        </div>

        <div>
          <h3>🌶️ Chili</h3>
          <p>Upload a chili leaf image for disease detection.</p>
        </div>
      </section>
    </div>
  );
}

export default Home;