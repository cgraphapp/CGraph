import React, { useState, useEffect, useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
export const ChatWindow = ({ roomId, roomName, isGroup }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [typing, setTyping] = useState(false);
    const messagesEndRef = useRef(null);
    // Fetch messages
    useEffect(() => {
        const fetchMessages = async () => {
            try {
                const response = await fetch(`/api/v1/messages/${roomId}`, {
                    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
                });
                const data = await response.json();
                setMessages(data.messages || []);
                scrollToBottom();
            }
            catch (error) {
                toast.error('Failed to load messages');
            }
        };
        fetchMessages();
        const interval = setInterval(fetchMessages, 2000); // Poll for new messages
        return () => clearInterval(interval);
    }, [roomId]);
    // WebSocket connection for real-time
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${roomId}?token=${token}`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'message') {
                setMessages((prev) => [...prev, data.message]);
                scrollToBottom();
            }
        };
        return () => ws.close();
    }, [roomId]);
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim())
            return;
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/messages/${roomId}/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
                },
                body: JSON.stringify({ content: newMessage }),
            });
            if (!response.ok)
                throw new Error('Failed to send message');
            setNewMessage('');
            toast.success('Message sent');
        }
        catch (error) {
            toast.error('Failed to send message');
        }
        finally {
            setLoading(false);
        }
    };
    return (<div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900">{roomName}</h2>
        {typing && <p className="text-sm text-gray-500">Someone is typing...</p>}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (<div key={msg.id} className="flex gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
              {msg.author_name}
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span className="font-semibold text-gray-900">{msg.author_name}</span>
                <span className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
                </span>
              </div>
              <p className="text-gray-700 mt-1">{msg.content}</p>
            </div>
          </div>))}
        <div ref={messagesEndRef}/>
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-3">
          <input type="text" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Type a message..." className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"/>
          <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-6 rounded-lg transition">
            Send
          </button>
        </div>
      </form>
    </div>);
};
