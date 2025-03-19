const admin = require("../config/firebase");

async function verifyFirebaseToken(req, res, next) {
    const token = req.headers.authorization?.split(" ")[1]; // Extract token after "Bearer "
    if (!token) return res.status(401).json({ error: "No token provided" });

    try {
        req.user = await admin.auth().verifyIdToken(token); // Store user data in request
        next();
    } catch (error) {
        res.status(401).json({ error: "Invalid Firebase token" });
    }
}

module.exports = verifyFirebaseToken;
