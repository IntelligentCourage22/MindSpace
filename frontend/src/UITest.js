import React from 'react';
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

export default UITest;