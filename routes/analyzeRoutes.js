const express = require("express");
const path = require("path");
require("dotenv").config();

const analyzeRoutes = require("./routes/analyzeRoutes");

const app = express();


// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));


// EJS
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));


// Static files
app.use(express.static(path.join(__dirname, "public")));


// Home page
app.get("/", (req, res) => {
    res.render("index");
});


// Analysis API
app.use("/analyze", analyzeRoutes);


const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});