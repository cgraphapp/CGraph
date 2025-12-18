import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import apiClient from '../../services/api';

interface Message {
  id: string;
  sender_id: string;
  content: string;
  created_at: string;
}

interface ChatWindowProps {
  conversationId: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ conversationId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const { data: messagesData } = useQuery(
    ['messages', conversationId],
    () => apiClient.get(`/api/v1/messages/dm/${conversationId}`).then(r => r.data),
  );
  
  useEffect(() => {
    if (messagesData) {
      setMessages(messagesData.messages);
    }
  }, [messagesData]);
  
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    
    try {
      const response = await apiClient.post(`/api/v1/messages/dm/${conversationId}/send`, {
        content: inputValue,
      });
      setMessages([...messages, response.data.message]);
      setInputValue('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className="p-2 bg-gray-100 rounded">
            <p className="text-sm text-gray-500">{msg.sender_id}</p>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="flex gap-2 p-4 border-t">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type message..."
          className="flex-1 px-4 py-2 border rounded-lg"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg"
        >
          Send
        </button>
      </form>
    </div>
  );
};
