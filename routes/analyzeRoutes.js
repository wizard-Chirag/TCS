const express = require("express");
const router = express.Router();

const { analyzeResearchQuestion } = require("../controllers/analyzeController");

router.post("/", analyzeResearchQuestion);

module.exports = router;