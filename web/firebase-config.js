// Firebase Configuration
// JIRA Duplicate Detection Project
const firebaseConfig = {
    apiKey: "AIzaSyCgjcibKokZodcMY_L3NP9Q4vM4kt4tZgs",
    authDomain: "jira-duplicate-detection.firebaseapp.com",
    projectId: "jira-duplicate-detection",
    storageBucket: "jira-duplicate-detection.firebasestorage.app",
    messagingSenderId: "892110955459",
    appId: "1:892110955459:web:5032050c5563ba449f9376",
    measurementId: "G-623M713T4M"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Firebase services
const auth = firebase.auth();
// Note: Firestore not used - data stored in backend

// Optional: Initialize Analytics
try {
    const analytics = firebase.analytics();
    console.log('📊 Firebase Analytics initialized');
} catch (e) {
    console.log('⚠️ Analytics not available');
}

console.log('🔥 Firebase initialized successfully!');
console.log('✅ Project: jira-duplicate-detection');
console.log('✅ Authentication: Ready');

