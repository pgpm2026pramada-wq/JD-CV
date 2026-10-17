import "dotenv/config";
import express from "express";
import multer from "multer";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { extractTextFromFile } from "./lib/extract.js";
import { analyzeJdCv, researchCompany } from "./lib/gemini.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: "4mb" }));
app.use(express.static(path.join(__dirname, "public")));

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 15 * 1024 * 1024 }, // 15 MB
});

// Health / config check.
app.get("/api/health", (req, res) => {
  const keySet =
    !!process.env.GEMINI_API_KEY &&
    process.env.GEMINI_API_KEY !== "your_api_key_here";
  res.json({ ok: true, keyConfigured: keySet, model: process.env.GEMINI_MODEL || "gemini-2.5-flash" });
});

// Extract text from an uploaded file (used by the front-end before analysis).
app.post("/api/extract", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No file uploaded." });
    const text = await extractTextFromFile(req.file);
    if (!text || text.replace(/\s/g, "").length < 20) {
      return res.status(422).json({
        error:
          "Couldn't extract readable text from that file. Try a different format or paste the text directly.",
      });
    }
    res.json({ text, filename: req.file.originalname });
  } catch (err) {
    res.status(422).json({ error: err.message || "Failed to read the file." });
  }
});

// Main analysis: JD + CV -> structured report, then grounded company research.
app.post("/api/analyze", async (req, res) => {
  const { jdText, cvText } = req.body || {};
  if (!jdText || jdText.trim().length < 40) {
    return res.status(400).json({ error: "Please provide a job description (at least a few lines)." });
  }
  if (!cvText || cvText.trim().length < 40) {
    return res.status(400).json({ error: "Please provide a CV (at least a few lines)." });
  }

  try {
    const analysis = await analyzeJdCv(jdText, cvText);

    // Grounded research is best-effort — don't fail the whole report if it errors.
    let research = { markdown: "", sources: [], company: analysis?.jd?.company || null, error: null };
    try {
      research = await researchCompany(
        analysis?.jd?.company,
        analysis?.jd?.industry,
        analysis?.jd?.title
      );
    } catch (err) {
      research.error = err.message || "Company research unavailable.";
    }

    res.json({ analysis, research });
  } catch (err) {
    console.error("Analysis failed:", err);
    res.status(500).json({ error: err.message || "Analysis failed. Please try again." });
  }
});

app.listen(PORT, () => {
  console.log(`\n  CareerMatch AI running at http://localhost:${PORT}\n`);
  const keySet =
    !!process.env.GEMINI_API_KEY &&
    process.env.GEMINI_API_KEY !== "your_api_key_here";
  if (!keySet) {
    console.log("  ⚠  GEMINI_API_KEY not set — copy .env.example to .env and add your key.\n");
  }
});
