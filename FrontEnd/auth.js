// Import Firebase modules
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

// ✅ Your Firebase Configuration (Replace with your actual config)
const firebaseConfig = {
    apiKey: "AIzaSyAEMGHk81mx50-8RLpQiapXA1VOBmTLYW4",
    authDomain: "landit-9217d.firebaseapp.com",
    projectId: "landit-9217d",
    storageBucket: "landit-9217d.firebasestorage.app",
    messagingSenderId: "592365237906",
    appId: "1:592365237906:web:acdb4d8e34e64825a2584b",
    measurementId: "G-70S5J38JHV"
};


// ✅ Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// ✅ Signup Function
export async function signup(email, password) {
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        return userCredential.user;
    } catch (error) {
        console.error("Signup Error:", error.message);
        throw error;
    }
}

// ✅ Login Function
export async function login(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        const token = await user.getIdToken();  // 🔹 Get Firebase ID Token

        // Store token in localStorage for API requests
        localStorage.setItem("firebaseToken", token);
        console.log("Login successful:", user.email);
        return user;
    } catch (error) {
        console.error("Login Error:", error.message);
        throw error;
    }
}

// ✅ Logout Function
export async function logout() {
    try {
        await signOut(auth);
        localStorage.removeItem("firebaseToken");
        console.log("User logged out");
    } catch (error) {
        console.error("Logout Error:", error.message);
        throw error;
    }
}

// ✅ Auth State Change Listener (Keeps track of user state)
export function onAuthChange(callback) {
    onAuthStateChanged(auth, (user) => {
        if (user) {
            console.log("User is logged in:", user.email);
        } else {
            console.log("No user logged in");
        }
        callback(user);
    });
}
