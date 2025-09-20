#!/usr/bin/env node
/**
 * Setup script for MindSpace frontend
 * Run this script to set up the development environment
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function runCommand(command, description) {
    console.log(`🔄 ${description}...`);
    try {
        execSync(command, { stdio: 'inherit' });
        console.log(`✅ ${description} completed successfully`);
        return true;
    } catch (error) {
        console.error(`❌ ${description} failed:`, error.message);
        return false;
    }
}

function createEnvFile() {
    const envContent = `# Frontend Environment Variables
REACT_APP_API_URL=http://localhost:8000/api

# For production, set this to your deployed backend URL
# REACT_APP_API_URL=https://your-backend-url.com/api
`;

    const envPath = path.join(__dirname, '.env');
    if (!fs.existsSync(envPath)) {
        fs.writeFileSync(envPath, envContent);
        console.log('✅ Created .env file with default settings');
    } else {
        console.log('⚠️  .env file already exists, skipping creation');
    }
}

function setupFrontend() {
    console.log('🚀 Setting up MindSpace Frontend...');
    
    // Install dependencies
    if (!runCommand('npm install', 'Installing Node.js dependencies')) {
        return false;
    }
    
    // Create .env file
    createEnvFile();
    
    console.log('\n🎉 Frontend setup completed successfully!');
    console.log('\n📋 Next steps:');
    console.log('1. Start the development server: npm start');
    console.log('2. Visit http://localhost:3000 to view the application');
    console.log('3. Make sure the backend is running on http://localhost:8000');
    console.log('4. Update .env file if your backend runs on a different port');
    
    return true;
}

if (require.main === module) {
    if (setupFrontend()) {
        process.exit(0);
    } else {
        process.exit(1);
    }
}

module.exports = { setupFrontend };
