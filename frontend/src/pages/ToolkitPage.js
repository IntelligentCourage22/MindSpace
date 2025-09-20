import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Settings } from 'lucide-react';

const ToolkitPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Settings className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Wellness Toolkit</h1>
          <p className="text-muted-foreground">Tools and resources for your mental wellness</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Wellness Toolkit</CardTitle>
          <CardDescription>
            This page will contain guided meditations, breathing exercises, and mental health resources.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Coming soon: Guided meditations, breathing timer, curated resources, and wellness exercises.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ToolkitPage;
