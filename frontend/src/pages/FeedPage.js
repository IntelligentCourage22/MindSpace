import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Heart } from 'lucide-react';

const FeedPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Heart className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Community Feed</h1>
          <p className="text-muted-foreground">Connect with others on their wellness journey</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Community Feed</CardTitle>
          <CardDescription>
            This page will contain the community feed with posts, reactions, and comments.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Coming soon: Anonymous posts, reaction buttons, comments, and community features.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default FeedPage;
