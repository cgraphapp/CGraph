import React, { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

interface Post {
  id: string;
  author_id: string;
  author_name: string;
  content: string;
  created_at: string;
  likes: number;
  position: number;
}

interface Thread {
  id: string;
  title: string;
  content: string;
  author_name: string;
  created_at: string;
  reply_count: number;
  view_count: number;
  is_pinned: boolean;
  is_locked: boolean;
}

interface ThreadViewProps {
  threadId: string;
}

export const ThreadView: React.FC<ThreadViewProps> = ({ threadId }) => {
  const [thread, setThread] = useState<Thread | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [replyText, setReplyText] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchThread = async () => {
      try {
        const response = await fetch(`/api/v1/forums/threads/${threadId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        });
        const data = await response.json();
        setThread(data.thread);
        setPosts(data.posts || []);
      } catch (error) {
        toast.error('Failed to load thread');
      } finally {
        setLoading(false);
      }
    };

    fetchThread();
  }, [threadId]);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim()) return;

    try {
      const response = await fetch(`/api/v1/forums/threads/${threadId}/reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ content: replyText }),
      });

      if (!response.ok) throw new Error('Failed to post reply');

      setReplyText('');
      toast.success('Reply posted!');
      
      // Refresh posts
      const threadsResponse = await fetch(`/api/v1/forums/threads/${threadId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      const data = await threadsResponse.json();
      setPosts(data.posts || []);
    } catch (error) {
      toast.error('Failed to post reply');
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;
  if (!thread) return <div className="text-center py-8">Thread not found</div>;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Thread Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">{thread.title}</h1>
          {thread.is_pinned && <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">📌 Pinned</span>}
        </div>
        
        <div className="flex gap-4 text-sm text-gray-600 mb-4">
          <span>👤 {thread.author_name}</span>
          <span>📅 {formatDistanceToNow(new Date(thread.created_at), { addSuffix: true })}</span>
          <span>👁️ {thread.view_count} views</span>
          <span>💬 {thread.reply_count} replies</span>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700">
          {thread.content}
        </div>
      </div>

      {/* Posts */}
      <div className="space-y-4 mb-8">
        {posts.map((post) => (
          <div key={post.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold flex-shrink-0">
                {post.author_name}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-900">{post.author_name}</span>
                  <span className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                  </span>
                </div>
                
                <p className="text-gray-700 mb-3">{post.content}</p>
                
                <div className="flex gap-3">
                  <button className="text-sm text-gray-600 hover:text-blue-600">
                    👍 {post.likes > 0 ? post.likes : 'Like'}
                  </button>
                  <button className="text-sm text-gray-600 hover:text-blue-600">
                    💬 Reply
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Reply Form */}
      {!thread.is_locked && (
        <form onSubmit={handleReply} className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Post a Reply</h3>
          
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Write your reply here..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical min-h-[120px]"
          />
          
          <button
            type="submit"
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition"
          >
            Post Reply
          </button>
        </form>
      )}
    </div>
  );
};

