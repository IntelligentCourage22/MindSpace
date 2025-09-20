import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { BookOpen } from 'lucide-react';

const JournalPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <BookOpen className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Journal</h1>
          <p className="text-muted-foreground">Track your thoughts and emotions</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Journal Feature</CardTitle>
          <CardDescription>
            This page will contain the journaling interface with mood tracking, entry creation, and analytics.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Coming soon: Journal entry form, mood picker, calendar view, and mood analytics.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default JournalPage;
