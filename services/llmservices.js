// =====================================================
// Generic LLM API caller
// =====================================================

async function callLLM(messages) {

    const response =
        await fetch(
            process.env.LLM_API_URL,
            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json",

                    "Authorization":
                        `Bearer ${process.env.LLM_API_KEY}`

                },

                body: JSON.stringify({

                    model:
                        process.env.LLM_MODEL,

                    messages,

                    temperature: 0.2,

                    response_format: {
                        type: "json_object"
                    }

                })

            }
        );


    if (!response.ok) {

        const errorText =
            await response.text();


        throw new Error(
            `LLM API request failed: ${errorText}`
        );

    }


    const data =
        await response.json();


    // ---------------------------------------------
    // OpenAI-compatible response
    // ---------------------------------------------

    const content =
        data
            ?.choices?.[0]
            ?.message?.content;


    if (!content) {

        throw new Error(
            "LLM returned an empty response"
        );

    }


    return parseJSON(content);

}



// =====================================================
// Parse JSON returned by LLM
// =====================================================

function parseJSON(content) {

    try {

        return JSON.parse(content);

    }

    catch (error) {

        // Sometimes models return:
        //
        // ```json
        // {...}
        // ```
        //
        // Remove markdown wrapper.

        const cleaned =
            content
                .replace(/^```json\s*/i, "")
                .replace(/^```\s*/i, "")
                .replace(/\s*```$/i, "")
                .trim();


        try {

            return JSON.parse(cleaned);

        }

        catch (secondError) {

            console.error(
                "Invalid JSON returned by LLM:"
            );

            console.error(content);


            throw new Error(
                "LLM returned invalid JSON"
            );

        }

    }

}



// =====================================================
// STEP 1
// Extract structured evidence
// =====================================================

async function extractEvidence(
    question,
    papers
) {

    const prompt = `

You are a medical literature evidence extraction
assistant.

Your task is to extract evidence from the provided
medical research paper abstracts.

Research question:

${question}


Papers:

${JSON.stringify(papers, null, 2)}


For EVERY paper, extract:

1. PMID
2. Population
3. Intervention or exposure
4. Comparison
5. Outcome
6. Key finding
7. Evidence strength
8. Limitations


IMPORTANT RULES:

- Use ONLY information contained in the provided
  paper data.
- Do NOT invent information.
- Do NOT use outside medical knowledge.
- If information is missing, write "Not reported".
- Do not make a clinical recommendation.
- Preserve uncertainty when the paper is uncertain.
- Evidence strength should be based only on what
  can reasonably be determined from the abstract.


Return ONLY valid JSON.

Use this exact structure:

{
    "evidence": [
        {
            "pmid": "",
            "population": "",
            "intervention": "",
            "comparison": "",
            "outcome": "",
            "key_finding": "",
            "evidence_strength": "",
            "limitations": ""
        }
    ]
}

`;


    const result =
        await callLLM([

            {
                role: "system",

                content:
                    "You extract medical evidence accurately and conservatively."
            },

            {
                role: "user",

                content: prompt
            }

        ]);


    // ---------------------------------------------
    // Ensure expected structure
    // ---------------------------------------------

    if (!Array.isArray(result.evidence)) {

        throw new Error(
            "LLM evidence response has invalid format"
        );

    }


    return result.evidence;

}



// =====================================================
// STEP 2
// Synthesize evidence
// =====================================================

async function synthesizeEvidence(
    question,
    evidence
) {

    const prompt = `

You are a medical literature synthesis assistant.

Research question:

${question}


Structured evidence extracted from PubMed papers:

${JSON.stringify(evidence, null, 2)}


Create an overall synthesis of the available
evidence.


Your synthesis must contain:

1. A direct answer to the research question.
2. The major findings across studies.
3. Overall evidence assessment.
4. Important limitations.
5. Confidence level.


IMPORTANT RULES:

- Use ONLY the structured evidence provided.
- Do NOT introduce outside medical facts.
- Do NOT invent results.
- Do NOT give personalized medical advice.
- If studies disagree, explicitly mention the disagreement.
- If evidence is weak or insufficient, say so.
- Do not claim causation unless the evidence supports it.


Return ONLY valid JSON.

Use exactly this structure:

{
    "answer": "",
    "key_findings": [],
    "overall_evidence": "",
    "limitations": [],
    "confidence": ""
}

`;


    const result =
        await callLLM([

            {
                role: "system",

                content:
                    "You synthesize medical research evidence conservatively and accurately."
            },

            {
                role: "user",

                content: prompt
            }

        ]);


    // ---------------------------------------------
    // Validate response
    // ---------------------------------------------

    if (
        !result ||
        typeof result.answer !== "string"
    ) {

        throw new Error(
            "LLM synthesis response has invalid format"
        );

    }


    if (
        !Array.isArray(
            result.key_findings
        )
    ) {

        result.key_findings = [];

    }


    if (
        !Array.isArray(
            result.limitations
        )
    ) {

        result.limitations = [];

    }


    return result;

}



// =====================================================
// Export
// =====================================================

module.exports = {

    extractEvidence,

    synthesizeEvidence

};