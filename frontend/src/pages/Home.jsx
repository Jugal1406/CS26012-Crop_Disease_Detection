import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import PlantJourney from "../components/PlantJourney";
import HowItWorks from "../components/HowItWorks";
import CropCards from "../components/CropCards";
import Technology from "../components/Technology";
import DemoSection from "../components/DemoSection";
import FinalCTA from "../components/FinalCTA";
import Footer from "../components/Footer";
import { useTranslation } from "../context/LanguageContext";
import "../styles/landing.css";

function Home() {
  const { t } = useTranslation();

  return (
    <div className="landing">
      <a href="#main" className="lp-skip">
        {t("landing.skipToContent", "Skip to content")}
      </a>
      <Navbar />
      <main id="main">
        <Hero />
        <PlantJourney />
        <HowItWorks />
        <CropCards />
        <Technology />
        <DemoSection />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

export default function HomePage() {
  return <Home />;
}
