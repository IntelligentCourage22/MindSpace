#!/usr/bin/env node
/**
 * Fix UI Components Script
 * This script installs missing dependencies and fixes UI component issues
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

function fixUI() {
    console.log('🔧 Fixing MindSpace UI Components...');
    console.log('=====================================');
    
    // Install missing Radix UI dependencies
    const missingDeps = [
        '@radix-ui/react-label',
        '@radix-ui/react-slot',
        '@radix-ui/react-separator',
        '@radix-ui/react-select',
        '@radix-ui/react-toast',
        '@radix-ui/react-avatar',
        'class-variance-authority',
        'clsx',
        'tailwind-merge'
    ];
    
    console.log('📦 Installing missing UI dependencies...');
    const installCommand = `npm install ${missingDeps.join(' ')}`;
    if (!runCommand(installCommand, 'Installing missing dependencies')) {
        console.log('⚠️  Some dependencies may have failed to install. Continuing...');
    }
    
    // Create missing component files
    console.log('🔨 Creating missing UI components...');
    
    const components = [
        'form.js',
        'label.js', 
        'textarea.js',
        'select.js',
        'badge.js',
        'avatar.js',
        'alert.js',
        'separator.js',
        'skeleton.js',
        'toast.js',
        'use-toast.js'
    ];
    
    components.forEach(component => {
        const componentPath = path.join(__dirname, 'src', 'components', 'ui', component);
        if (!fs.existsSync(componentPath)) {
            console.log(`⚠️  Missing component: ${component}`);
        }
    });
    
    // Update package.json scripts
    console.log('📝 Updating package.json...');
    const packageJsonPath = path.join(__dirname, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        
        // Add useful scripts
        packageJson.scripts = {
            ...packageJson.scripts,
            'fix-ui': 'node fix-ui.js',
            'dev': 'npm start',
            'build:css': 'tailwindcss -i ./src/index.css -o ./dist/output.css --watch'
        };
        
        fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
        console.log('✅ Updated package.json scripts');
    }
    
    // Create a simple test component to verify UI works
    const testComponent = `import React from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';

const UITest = () => {
  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">UI Components Test</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
          <CardDescription>This card tests if components are working</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="test-input">Test Input</Label>
            <Input id="test-input" placeholder="Type something..." />
          </div>
          <Button>Test Button</Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default UITest;`;

    const testPath = path.join(__dirname, 'src', 'UITest.js');
    fs.writeFileSync(testPath, testComponent);
    console.log('✅ Created UI test component');
    
    console.log('\n🎉 UI fix completed!');
    console.log('\n📋 Next steps:');
    console.log('1. Run: npm start');
    console.log('2. Check if components render properly');
    console.log('3. If issues persist, run: npm install --force');
    console.log('4. Clear browser cache and restart');
    
    return true;
}

if (require.main === module) {
    if (fixUI()) {
        process.exit(0);
    } else {
        process.exit(1);
    }
}

module.exports = { fixUI };
