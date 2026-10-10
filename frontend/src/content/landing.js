/*
 * All landing-page text and data in one place, so the components stay purely visual.
 */

/* ----------------------------------------------------------------------------
 * OPTIONAL PHOTOS
 * The page is fully illustrated without any photos. To use real photography, put the
 * image in src/assets/landing/ , import it here and replace `null`, e.g.
 *   import chiliLeaf from "../assets/landing/chili-leaf.jpg";
 *   demoLeaf: chiliLeaf,
 * Tips: JPG/WebP, max ~1600px wide (hero/CTA) or ~900px (cards), under ~300 KB each.
 * Good sources: your own field photos, the project datasets (check their licence and
 * credit them), Unsplash / Pexels.
 * ------------------------------------------------------------------------- */
export const MEDIA = {
  heroBackdrop: null, // wide crop field at dawn/golden hour — sits behind the growing plant
  demoLeaf: null, // close-up of a diseased chili leaf, roughly square
  finalBackdrop: null, // wide crop field, used behind the final call-to-action
  crops: {
    potato: null,
    groundnut: null,
    chili: null,
  },
};

export const GITHUB_URL = "https://github.com/Jugal1406/CS26012-Crop_Disease_Detection";

/* ---------------------------------------------------------------- hero journey */

/** Stages of the scroll-driven hero animation. `from` = scroll progress where the stage starts. */
export const HERO_STAGES = [
  { from: 0, name: "Seed", line: "Every harvest begins beneath the soil." },
  { from: 0.08, name: "Sprout", line: "A seedling breaks through and opens its first leaves." },
  { from: 0.27, name: "Young plant", line: "True leaves unfold, and the plant starts feeding itself." },
  { from: 0.41, name: "Growing crop", line: "The canopy fills in, and with it the risk of disease." },
  { from: 0.56, name: "Mature crop", line: "A healthy chili plant, flowering and bearing fruit." },
  { from: 0.71, name: "Leaf inspection", line: "Up close, the first symptoms often show on a single leaf." },
  { from: 0.83, name: "AI detection", line: "One photo. A clear, confident diagnosis." },
];

/** What the illustrative result card in the hero and demo shows. */
export const DEMO_RESULT = {
  crop: "Chili",
  disease: "Cercospora Leaf Spot",
  confidence: 96,
};

/* ---------------------------------------------------------------- seed to harvest */

/** `progress` = growth value passed to the plant drawing; `view` = which part of it to frame. */
export const LIFECYCLE = [
  {
    name: "Seed",
    text: "Good seed and living soil set the ceiling for every harvest.",
    progress: 0.03,
    view: [254, 552, 92, 92],
  },
  {
    name: "Sprout",
    text: "The first days decide vigour, and seedlings are at their most fragile.",
    progress: 0.3,
    view: [214, 482, 172, 172],
  },
  {
    name: "Young Plant",
    text: "True leaves appear. This is where early stress first becomes visible.",
    progress: 0.43,
    view: [130, 372, 340, 340],
  },
  {
    name: "Growing Crop",
    text: "A denser canopy holds humidity, which many leaf diseases need to spread.",
    progress: 0.57,
    view: [60, 220, 480, 480],
  },
  {
    name: "Mature Crop",
    text: "Flowering and fruiting. Losses at this stage cost the most.",
    progress: 0.72,
    view: [10, 80, 580, 580],
  },
  {
    name: "Leaf Analysis",
    text: "A single leaf photo can reveal what is easy to miss by eye.",
    leaf: true,
  },
];

/* ---------------------------------------------------------------- how it works */

export const STEPS = [
  {
    icon: "crop",
    title: "Select your crop",
    text: "Choose potato, groundnut or chili so the right crop-specific model is used.",
  },
  {
    icon: "upload",
    title: "Upload a leaf image",
    text: "Take a photo in the field or upload one from your phone or computer.",
  },
  {
    icon: "scan",
    title: "AI analyzes the image",
    text: "A deep learning model examines colour, texture and lesion patterns on the leaf.",
  },
  {
    icon: "tag",
    title: "Receive a prediction",
    text: "The most likely disease, or a healthy result, for that crop is identified.",
  },
  {
    icon: "report",
    title: "View confidence & details",
    text: "See how confident the model is, along with diagnostic information.",
  },
];

/* ---------------------------------------------------------------- crops */

export const CROPS = [
  {
    id: "potato",
    name: "Potato",
    latin: "Solanum tuberosum",
    origin: "Field images · Uttar Pradesh",
    classes: 3,
    leaf: "potato",
  },
  {
    id: "groundnut",
    name: "Groundnut",
    latin: "Arachis hypogaea",
    origin: "Field images · VIT Chennai dataset",
    classes: 6,
    leaf: "groundnut",
  },
  {
    id: "chili",
    name: "Chili",
    latin: "Capsicum annuum",
    origin: "Field images · Deccan Plateau",
    classes: 6,
    leaf: "chili",
  },
];

export const PLANNED_CROPS = ["Rice", "Wheat", "Tomato", "Banana", "Soyabean"];

/* ---------------------------------------------------------------- technology */

export const TECH = [
  { icon: "layers", name: "TensorFlow / Keras", role: "Model training" },
  { icon: "net", name: "MobileNetV2", role: "Lightweight CNN, adapted to each crop by transfer learning" },
  { icon: "bolt", name: "FastAPI", role: "Serves predictions from the trained models" },
  { icon: "window", name: "React", role: "The web interface you are using" },
];

export const REPORT_ITEMS = [
  "Disease description",
  "Organic treatment",
  "Chemical treatment",
  "Prevention tip",
  "Downloadable PDF",
];
