import { useState } from "react";

function Diagnose() {
  const [crop, setCrop] = useState("");
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageChange = (event) => {
    const selectedImage = event.target.files[0];

    if (selectedImage) {
      setImage(selectedImage);
      setResult(null);
    }
  };

  const handlePredict = async () => {
    if (!crop || !image) {
      return;
    }

    setLoading(true);

    const formData = new FormData();

    formData.append("crop", crop);
    formData.append("image", image);

    try {
      const response = await fetch("http://localhost:8000/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      setResult(data);
    } catch (error) {
      console.error(error);
      setResult({
        error: "Could not connect to the backend.",
      });
    }

    setLoading(false);
  };

  return (
    <div>
      <h1>Diagnose Plant Disease</h1>

      <p>
        Select the crop and upload an image of its leaf.
      </p>

      <div>
        <label>Select Crop: </label>

        <select
          value={crop}
          onChange={(event) => setCrop(event.target.value)}
        >
          <option value="">-- Select Crop --</option>
          <option value="potato">Potato</option>
          <option value="groundnut">Groundnut</option>
          <option value="chili">Chili</option>
        </select>
      </div>

      <br />

      <div>
        <label>Upload Leaf Image: </label>

        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
        />
      </div>

      <br />

      {image && (
        <div>
          <h3>Selected Image:</h3>

          <img
            src={URL.createObjectURL(image)}
            alt="Selected crop leaf"
            width="300"
          />
        </div>
      )}

      <br />

      <button
        onClick={handlePredict}
        disabled={!crop || !image || loading}
      >
        {loading ? "Predicting..." : "Predict Disease"}
      </button>

      {result && (
        <div>
          <h2>Prediction Result</h2>

          {result.error ? (
            <p>{result.error}</p>
          ) : (
            <>
              <p>Crop: {result.crop}</p>

              <p>Image: {result.filename}</p>

              <p>Disease: {result.disease}</p>

              <p>Confidence: {result.confidence}%</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default Diagnose;