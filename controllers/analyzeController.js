const {
    searchPubMed
} = require("../services/pubmedService");

const {
    extractEvidence,
    synthesizeEvidence
} = require("../services/llmService");


async function analyzeResearchQuestion(req, res) {

    try {

        const { question } = req.body;


        // -------------------------------
        // Validate input
        // -------------------------------

        if (!question || question.trim() === "") {

            return res.status(400).json({
                error: "Research question is required"
            });

        }


        console.log("Research question:", question);


        // -------------------------------
        // STEP 1
        // Search PubMed
        // -------------------------------

        console.log("Searching PubMed...");

        const papers =
            await searchPubMed(question);


        if (papers.length === 0) {

            return res.status(404).json({
                error: "No relevant papers found"
            });

        }


        console.log(
            `Found ${papers.length} papers`
        );


        // -------------------------------
        // STEP 2
        // Evidence extraction
        // -------------------------------

        console.log(
            "Extracting evidence..."
        );

        const evidence =
            await extractEvidence(
                question,
                papers
            );


        // -------------------------------
        // STEP 3
        // Synthesis
        // -------------------------------

        console.log(
            "Generating synthesis..."
        );

        const synthesis =
            await synthesizeEvidence(
                question,
                evidence
            );


        // -------------------------------
        // FINAL RESPONSE
        // -------------------------------

        return res.json({

            papers: papers,

            evidence: evidence,

            synthesis: synthesis

        });

    }

    catch (error) {

        console.error(error);

        return res.status(500).json({

            error:
                "Failed to analyze research question",

            message:
                error.message

        });

    }

}


module.exports = {
    analyzeResearchQuestion
};