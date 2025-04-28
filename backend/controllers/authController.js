exports.login = async (req, res) => {
    const { email, password } = req.body;

    // Example logic
    if (email === 'test@example.com' && password === '123456') {
        return res.status(200).json({ success: true, message: "Login successful" });
    } else {
        return res.status(401).json({ success: false, message: "Invalid credentials" });
    }
};
