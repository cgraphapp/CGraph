import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
export const ForumList = () => {
    const [forums, setForums] = useState([]);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        const fetchForums = async () => {
            try {
                const response = await fetch('/api/v1/forums', {
                    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
                });
                const data = await response.json();
                setForums(data.forums || []);
            }
            catch (error) {
                toast.error('Failed to load forums');
            }
            finally {
                setLoading(false);
            }
        };
        fetchForums();
    }, []);
    if (loading)
        return <div className="text-center py-8">Loading forums...</div>;
    return (<div className="max-w-6xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Forums</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {forums.map((forum) => (<div key={forum.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">{forum.name}</h2>
            <p className="text-gray-600 mb-4">{forum.description}</p>
            
            <div className="flex justify-between text-sm text-gray-500">
              <span>📝 {forum.total_posts} posts</span>
              <span>👥 {forum.total_members} members</span>
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {forum.category}
              </span>
            </div>
            
            <button className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition">
              Enter Forum
            </button>
          </div>))}
      </div>
    </div>);
};
