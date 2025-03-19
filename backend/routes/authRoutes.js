const express = require("express");
const admin = require("../config/firebase");
const verifyFirebaseToken = require("../middleware/authMiddleware");

const router = express.Router();

// 🔹 User Signup (Handled on Frontend)
router.post("/signup", async (req, res) => {
    const { email, password } = req.body;

    try {
        const user = await admin.auth().createUser({ email, password });
        res.status(201).json({ message: "User created successfully", user });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

// 🔹 User Login (Handled in Frontend)
router.post("/login", (req, res) => {
    res.status(200).json({ message: "Use Firebase SDK for login authentication" });
});

// 🔹 Get Authenticated User Data (Protected Route)
router.get("/user", verifyFirebaseToken, async (req, res) => {
    try {
        const user = await admin.auth().getUser(req.user.uid);
        res.json({ email: user.email, uid: user.uid, role: req.user.role || "user" });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
