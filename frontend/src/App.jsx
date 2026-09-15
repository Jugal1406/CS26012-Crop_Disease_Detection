import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Diagnose from "./pages/Diagnose";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Home />} />

        <Route path="/login" element={<Login />} />

        <Route path="/diagnose" element={<Diagnose />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;