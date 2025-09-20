import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MessageSquare } from 'lucide-react';

const ChatPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <MessageSquare className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Chat</h1>
          <p className="text-muted-foreground">Connect with peers and mentors</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Peer Support Chat</CardTitle>
          <CardDescription>
            This page will contain real-time chat functionality with peer support and mentoring.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Coming soon: Real-time messaging, room creation, peer matching, and support features.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatPage;
